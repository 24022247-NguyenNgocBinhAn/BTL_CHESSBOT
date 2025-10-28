import os
import sys
import threading
import traceback
import queue
import time
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox

try:
    import chess
    import chess.pgn
except Exception:
    print("Please install python-chess: pip install chess")
    sys.exit(1)

# PIL for image resizing (optional but recommended)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Try to import engine API
try:
    from src.search import find_best_move
    FIND_BEST_MOVE_AVAILABLE = True
except Exception:
    find_best_move = None
    FIND_BEST_MOVE_AVAILABLE = False

# Try to import GameState from engine (optional)
GameStateClass = None
try:
    from src.board import GameState as _GS
    GameStateClass = _GS
except Exception:
    GameStateClass = None

# --- UI constants ---
SQUARE_SIZE = 64
BOARD_COLOR_LIGHT = '#F0D9B5'
BOARD_COLOR_DARK = '#B58863'
HIGHLIGHT_COLOR = '#A9A9FF'
MOVE_COLOR = '#77DD77'

# piece file mapping (in ./pieces/)
PIECE_FILES = {
    (chess.WHITE, chess.PAWN): 'wP.png',
    (chess.WHITE, chess.KNIGHT): 'wN.png',
    (chess.WHITE, chess.BISHOP): 'wB.png',
    (chess.WHITE, chess.ROOK): 'wR.png',
    (chess.WHITE, chess.QUEEN): 'wQ.png',
    (chess.WHITE, chess.KING): 'wK.png',
    (chess.BLACK, chess.PAWN): 'bP.png',
    (chess.BLACK, chess.KNIGHT): 'bN.png',
    (chess.BLACK, chess.BISHOP): 'bB.png',
    (chess.BLACK, chess.ROOK): 'bR.png',
    (chess.BLACK, chess.QUEEN): 'bQ.png',
    (chess.BLACK, chess.KING): 'bK.png',
}


# ---------------------------
# Adapter to feed your engine
# ---------------------------
class _SearchGameStateAdapter:
    """
    Minimal adapter providing interface expected by engine code:
      - .board (a chess.Board instance)
      - get_legal_moves() -> list of chess.Move
      - make_move(move)
      - unmake_move()

    This adapter uses a separate internal board so the engine cannot mutate the GUI's board.
    """
    def __init__(self, board: chess.Board):
        # shallow copy is cheap; the engine will run on a separate board
        self.board = board.copy()

    def get_legal_moves(self):
        return list(self.board.legal_moves)

    def make_move(self, move: chess.Move):
        self.board.push(move)

    def unmake_move(self):
        self.board.pop()


def build_search_state(board: chess.Board):
    """
    Build an object acceptable to find_best_move:
      - If GameStateClass is importable and can be constructed from chess.Board, use it.
      - Otherwise fall back to adapter above.
    """
    if GameStateClass:
        try:
            try:
                return GameStateClass(board.copy())
            except Exception:
                return GameStateClass(board=board.copy())
        except Exception:
            return _SearchGameStateAdapter(board)
    else:
        return _SearchGameStateAdapter(board)


# ---------------------------
# Main GUI
# ---------------------------
class ChessGUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master or tk.Tk()
        self.master.title("Python-Chess — Optimized Image GUI")
        self.pack(fill='both', expand=True)

        # Model
        self.board = chess.Board()
        self.flipped = False
        self.human_side = 'both'  # 'white', 'black', or 'both'

        # selection
        self.selected_sq = None
        self.legal_moves = []  # list of chess.Move for selected square

        # UI caches
        self.images = {}        # (color, piece_type) -> PhotoImage
        self.piece_image_ids = {}  # sq -> canvas_image_id

        # Move list state (optimized incremental SAN appends)
        self.move_list_lines = []  # list of lines (strings)

        # AI
        self.ai_available = FIND_BEST_MOVE_AVAILABLE
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_max_depth = 3
        self.ai_time_limit = None
        self.ai_queue = queue.Queue()  # used to post AI moves back to main thread

        self._load_defaults()
        self.create_widgets()
        self.load_images()
        self.draw_board(full=True)
        self.update_move_list(full=True)

        # process AI queue periodically
        self.master.after(80, self._poll_ai_queue)

    def _load_defaults(self):
        self.window_width = 8 * SQUARE_SIZE + 300

    def create_widgets(self):
        self.canvas = tk.Canvas(self, width=8 * SQUARE_SIZE, height=8 * SQUARE_SIZE, bg='white', highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=12, padx=6, pady=6)
        self.canvas.bind("<Button-1>", self.on_click)

        # Controls
        tk.Button(self, text="New Game", command=self.new_game).grid(row=0, column=1, sticky='ew', padx=4, pady=2)
        tk.Button(self, text="Choose Side", command=self.choose_side_dialog).grid(row=1, column=1, sticky='ew', padx=4, pady=2)
        tk.Button(self, text="Undo", command=self.undo_move).grid(row=2, column=1, sticky='ew', padx=4, pady=2)
        tk.Button(self, text="Flip Board", command=self.flip_board).grid(row=3, column=1, sticky='ew', padx=4, pady=2)

        ai_frame = tk.LabelFrame(self, text="AI (src.search)", padx=6, pady=6)
        ai_frame.grid(row=4, column=1, sticky='nsew', padx=4, pady=6)

        self.ai_status_var = tk.StringVar(value="AI: unavailable" if not self.ai_available else "AI: ready")
        tk.Label(ai_frame, textvariable=self.ai_status_var).grid(row=0, column=0, columnspan=2, sticky='w')

        tk.Label(ai_frame, text="Max depth:").grid(row=1, column=0, sticky='w')
        self.depth_var = tk.IntVar(value=self.ai_max_depth)
        tk.Spinbox(ai_frame, from_=1, to=20, textvariable=self.depth_var, width=5, command=self._on_ai_param_change).grid(row=1, column=1, sticky='e')

        tk.Label(ai_frame, text="Time limit (s):").grid(row=2, column=0, sticky='w')
        self.time_var = tk.StringVar(value='' if self.ai_time_limit is None else str(self.ai_time_limit))
        tk.Entry(ai_frame, textvariable=self.time_var, width=6).grid(row=2, column=1, sticky='e')
        tk.Button(ai_frame, text="Apply", command=self._on_ai_param_change).grid(row=3, column=0, columnspan=2, pady=(6, 0))

        tk.Button(self, text="Save PGN", command=self.save_pgn).grid(row=5, column=1, sticky='ew', padx=4, pady=2)
        tk.Button(self, text="Load PGN", command=self.load_pgn).grid(row=6, column=1, sticky='ew', padx=4, pady=2)

        move_frame = tk.LabelFrame(self, text="Move list", padx=4, pady=4)
        move_frame.grid(row=7, column=1, rowspan=5, sticky='nsew', padx=4, pady=4)

        self.move_text = tk.Text(move_frame, width=32, height=18, wrap='none')
        self.move_text.pack(side='left', fill='both', expand=True)
        scroll = tk.Scrollbar(move_frame, command=self.move_text.yview)
        scroll.pack(side='right', fill='y')
        self.move_text.config(yscrollcommand=scroll.set, state='disabled')

        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

    def _on_ai_param_change(self):
        try:
            self.ai_max_depth = int(self.depth_var.get())
        except Exception:
            self.ai_max_depth = 3
        try:
            t = self.time_var.get().strip()
            self.ai_time_limit = None if t == '' else float(t)
        except Exception:
            self.ai_time_limit = None

    def load_images(self):
        base = os.path.join(os.path.dirname(__file__), 'pieces') if '__file__' in globals() else 'pieces'
        # Load once at startup; resize with PIL if available
        for key, filename in PIECE_FILES.items():
            path = os.path.join(base, filename)
            if os.path.exists(path):
                try:
                    if PIL_AVAILABLE:
                        img = Image.open(path).convert('RGBA')
                        img = img.resize((SQUARE_SIZE, SQUARE_SIZE), Image.LANCZOS)
                        self.images[key] = ImageTk.PhotoImage(img)
                    else:
                        self.images[key] = tk.PhotoImage(file=path)
                except Exception as e:
                    print(f"Failed to load {path}: {e}")
            else:
                print(f"Image not found: {path}")

    # --- coordinate helpers ---
    def coord_to_square(self, x, y):
        file = x // SQUARE_SIZE
        rank = y // SQUARE_SIZE
        if self.flipped:
            file = 7 - file
            rank = 7 - rank
        return chess.square(int(file), 7 - int(rank))

    def square_to_coord(self, sq):
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        if self.flipped:
            file = 7 - file
            rank = 7 - rank
        return file * SQUARE_SIZE, (7 - rank) * SQUARE_SIZE

    # --- drawing (optimized) ---
    def draw_board(self, full=False):
        """
        Draw board only when necessary. If full=True redraw squares and all pieces.
        Otherwise update highlights and moved pieces.
        """
        if full:
            self.canvas.delete('square')
            # draw squares once
            for rank in range(8):
                for file in range(8):
                    x1 = file * SQUARE_SIZE
                    y1 = rank * SQUARE_SIZE
                    x2 = x1 + SQUARE_SIZE
                    y2 = y1 + SQUARE_SIZE
                    color = BOARD_COLOR_LIGHT if (file + rank) % 2 == 0 else BOARD_COLOR_DARK
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='', tags=('square',))

            # draw coordinate labels
            self.canvas.delete('coords')
            for file in range(8):
                for rank in range(8):
                    x = file * SQUARE_SIZE
                    y = rank * SQUARE_SIZE
                    sq = chess.square(file, 7 - rank) if not self.flipped else chess.square(7-file, rank)
                    file_char = chess.square_name(sq)[0]
                    rank_char = chess.square_name(sq)[1]
                    if rank == 7:
                        self.canvas.create_text(x+5, y+SQUARE_SIZE-10, anchor='w', text=file_char, font=('Arial', 8), tags=('coords',))
                    if file == 0:
                        self.canvas.create_text(x+5, y+8, anchor='nw', text=rank_char, font=('Arial', 8), tags=('coords',))

            # draw pieces fresh
            # Clear any existing piece images
            for cid in list(self.piece_image_ids.values()):
                try:
                    self.canvas.delete(cid)
                except Exception:
                    pass
            self.piece_image_ids.clear()

            for sq in chess.SQUARES:
                piece = self.board.piece_at(sq)
                if piece:
                    x, y = self.square_to_coord(sq)
                    img = self.images.get((piece.color, piece.piece_type))
                    if img:
                        cid = self.canvas.create_image(x, y, anchor='nw', image=img, tags=('piece',))
                        self.piece_image_ids[sq] = cid
                    else:
                        # minimal fallback
                        cx = x + SQUARE_SIZE/2
                        cy = y + SQUARE_SIZE/2
                        cid = self.canvas.create_oval(cx-12, cy-12, cx+12, cy+12, fill='#fff' if piece.color==chess.WHITE else '#000', tags=('piece',))
                        self.canvas.create_text(cx, cy, text=piece.symbol().upper(), fill='#444', tags=('piece_text',))
        else:
            # update moved pieces only: remove all piece tags and redraw (cheap compared to recomputing SAN)
            # We still keep image objects and recreate canvas image items for changed squares.
            # For simplicity we clear piece items and redraw pieces; avoids complex bookkeeping and is fast.
            self.canvas.delete('piece')
            self.canvas.delete('piece_text')
            self.piece_image_ids.clear()
            for sq in chess.SQUARES:
                piece = self.board.piece_at(sq)
                if piece:
                    x, y = self.square_to_coord(sq)
                    img = self.images.get((piece.color, piece.piece_type))
                    if img:
                        cid = self.canvas.create_image(x, y, anchor='nw', image=img, tags=('piece',))
                        self.piece_image_ids[sq] = cid
                    else:
                        cx = x + SQUARE_SIZE/2
                        cy = y + SQUARE_SIZE/2
                        self.canvas.create_oval(cx-12, cy-12, cx+12, cy+12, fill='#fff' if piece.color==chess.WHITE else '#000', tags=('piece',))
                        self.canvas.create_text(cx, cy, text=piece.symbol().upper(), fill='#444', tags=('piece_text',))

        # highlights (selected square & move dots) are redrawn every time (small number of objects)
        self.canvas.delete('highlight')
        if self.selected_sq is not None:
            sx, sy = self.square_to_coord(self.selected_sq)
            self.canvas.create_rectangle(sx, sy, sx+SQUARE_SIZE, sy+SQUARE_SIZE, fill=HIGHLIGHT_COLOR, stipple='gray25', outline='', tags=('highlight',))
            for mv in self.legal_moves:
                tx, ty = self.square_to_coord(mv.to_square)
                cx = tx + SQUARE_SIZE/2
                cy = ty + SQUARE_SIZE/2
                self.canvas.create_oval(cx-8, cy-8, cx+8, cy+8, fill=MOVE_COLOR, outline='', tags=('highlight',))

    # --- input handling ---
    def on_click(self, event):
        if self.ai_thinking:
            return

        sq = self.coord_to_square(event.x, event.y)
        piece = self.board.piece_at(sq)

        # restrict by human_side
        if self.human_side in ('white', 'black'):
            if (self.board.turn == chess.WHITE and self.human_side != 'white') or \
               (self.board.turn == chess.BLACK and self.human_side != 'black'):
                return

        if self.selected_sq is None:
            # select
            if piece and piece.color == self.board.turn:
                self.selected_sq = sq
                # compute only legal moves for this square
                self.legal_moves = [m for m in self.board.legal_moves if m.from_square == sq]
            else:
                return
        else:
            # attempt move
            if sq == self.selected_sq:
                self.selected_sq = None
                self.legal_moves = []
            else:
                candidate = next((m for m in self.legal_moves if m.to_square == sq), None)
                if candidate:
                    if self.is_promotion_move(candidate):
                        promo_piece = self.ask_promotion(candidate.to_square, candidate.from_square)
                        if promo_piece is None:
                            self.selected_sq = None
                            self.legal_moves = []
                            self.draw_board(full=False)
                            return
                        candidate = chess.Move(candidate.from_square, candidate.to_square, promotion=promo_piece)

                    # push human move (fast)
                    self.board.push(candidate)
                    # append SAN incrementally (fast)
                    self._append_san(candidate)

                    # reset selection
                    self.selected_sq = None
                    self.legal_moves = []

                    # redraw pieces only (fast)
                    self.draw_board(full=False)
                    # ensure move list visible
                    self.move_text.see(tk.END)

                    if self.board.is_game_over():
                        self.on_game_over()
                    else:
                        if self.should_ai_move():
                            self.request_ai_move()
                else:
                    # change selection
                    if piece and piece.color == self.board.turn:
                        self.selected_sq = sq
                        self.legal_moves = [m for m in self.board.legal_moves if m.from_square == sq]
                    else:
                        self.selected_sq = None
                        self.legal_moves = []
        # update highlights
        self.draw_board(full=False)

    def is_promotion_move(self, move):
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(move.to_square)
            if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                return True
        return False

    def ask_promotion(self, to_square, from_square):
        dlg = tk.Toplevel(self.master)
        dlg.title('Choose promotion')
        dlg.transient(self.master)
        dlg.grab_set()
        chosen = {'val': None}
        def pick(ptype):
            chosen['val'] = ptype
            dlg.destroy()
        for i, p in enumerate([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]):
            img = self.images.get((self.board.turn, p))
            if img:
                tk.Button(dlg, image=img, command=lambda p=p: pick(p)).grid(row=0, column=i)
            else:
                tk.Button(dlg, text=chess.piece_symbol(p).upper(), width=6, command=lambda p=p: pick(p)).grid(row=0, column=i)
        self.master.wait_window(dlg)
        return chosen['val']

    def should_ai_move(self):
        if not self.ai_available:
            return False
        if self.human_side == 'both':
            return False
        if self.human_side == 'white' and self.board.turn == chess.BLACK:
            return True
        if self.human_side == 'black' and self.board.turn == chess.WHITE:
            return True
        return False

    def request_ai_move(self):
        if self.ai_thinking or not self.ai_available:
            return
        self.ai_thinking = True
        self.ai_status_var.set('AI: thinking...')
        self._on_ai_param_change()

        board_snapshot = self.board.copy()

        def _worker(snapshot, depth, time_limit, out_q):
            try:
                search_state = build_search_state(snapshot)
                mv = find_best_move(search_state, max_depth=depth, time_limit_seconds=time_limit)
                out_q.put(('move', mv))
            except Exception as e:
                out_q.put(('error', str(e)))
                traceback.print_exc()

        t = threading.Thread(target=_worker, args=(board_snapshot, self.ai_max_depth, self.ai_time_limit, self.ai_queue), daemon=True)
        t.start()
        self.ai_thread = t

        # --- FAILSAFE TIMEOUT WATCHDOG ---
        if self.ai_time_limit:
            def _timeout_watch():
                if self.ai_thinking and self.ai_thread and self.ai_thread.is_alive():
                    print("[AI] Time limit reached — stopping AI.")
                    self.ai_thinking = False
                    self.ai_status_var.set("AI: timeout")
            self.master.after(int((self.ai_time_limit + 1) * 1000), _timeout_watch)

    def _poll_ai_queue(self):
        try:
            while True:
                typ, payload = self.ai_queue.get_nowait()
                if typ == 'move':
                    mv = payload
                    if mv is None:
                        print('AI returned no move')
                    else:
                        try:
                            if not isinstance(mv, chess.Move):
                                mv = chess.Move.from_uci(str(mv))
                        except Exception:
                            print('AI returned invalid move:', mv)
                            mv = None

                        if mv is not None and mv in self.board.legal_moves:
                            self.board.push(mv)
                            self._append_san(mv)
                            self.draw_board(full=False)
                            if self.board.is_game_over():
                                self.on_game_over()
                        else:
                            print('AI returned illegal move:', mv)
                elif typ == 'error':
                    print('AI error:', payload)

                # reset status after each message
                self.ai_thinking = False
                self.ai_status_var.set('AI: ready' if self.ai_available else 'AI: unavailable')

        except queue.Empty:
            pass

        # --- AUTO RECOVER IF THREAD HANGS ---
        if self.ai_thinking and self.ai_thread and not self.ai_thread.is_alive():
            print("[AI] Thread ended unexpectedly or timeout expired. Resetting state.")
            self.ai_thinking = False
            self.ai_status_var.set('AI: ready')

        self.master.after(80, self._poll_ai_queue)

    # --- move list / UI helpers (fast incremental SAN appends) ---
    def _append_san(self, last_move: chess.Move):
        """
        Append SAN for last_move to the text widget incrementally (fast).
        """
        try:
            # Build SAN using a lightweight temporary board: reuse last move stack to avoid recomputing from start
            # But easiest correct approach is copy board and pop last to generate SAN
            tmp = self.board.copy()
            # tmp currently has the move already pushed; to get SAN we need a board before last move
            tmp.pop()
            san = tmp.san(last_move)
        except Exception:
            # fallback to UCI
            san = str(last_move)

        # Append to text widget in a quick way
        self.move_text.configure(state='normal')
        move_no = len(self.board.move_stack)
        if move_no % 2 == 1:
            # white move just added
            self.move_text.insert(tk.END, f"{(move_no+1)//2}. {san} ")
        else:
            # black move just added
            self.move_text.insert(tk.END, f"{san}\n")
        self.move_text.configure(state='disabled')
        self.move_text.see(tk.END)

    def update_move_list(self, full=False):
        if full:
            # Full render from scratch (used at load or new game)
            self.move_text.configure(state='normal')
            self.move_text.delete('1.0', tk.END)
            b = chess.Board()
            for i, mv in enumerate(self.board.move_stack):
                san = b.san(mv)
                b.push(mv)
                if i % 2 == 0:
                    self.move_text.insert(tk.END, f"{(i//2)+1}. {san} ")
                else:
                    self.move_text.insert(tk.END, f"{san}\n")
            self.move_text.configure(state='disabled')
            self.move_text.see(tk.END)
        else:
            # incremental handled elsewhere via _append_san
            pass

    def undo_move(self):
        if self.ai_thinking:
            return
        if self.board.move_stack:
            self.board.pop()
            # rebuild full move list (cheap for single undo)
            self.update_move_list(full=True)
            self.selected_sq = None
            self.legal_moves = []
            self.draw_board(full=False)

    def new_game(self):
        if self.ai_thinking:
            messagebox.showinfo("Please wait", "AI is thinking. Try again later.")
            return
        if messagebox.askyesno("New Game", "Start a new game?"):
            self.board.reset()
            self.selected_sq = None
            self.legal_moves = []
            self.draw_board(full=True)
            self.update_move_list(full=True)
            if self.should_ai_move():
                self.request_ai_move()

    def choose_side_dialog(self):
        dlg = tk.Toplevel(self.master)
        dlg.title("Choose Side")
        dlg.transient(self.master)
        dlg.grab_set()
        choice = {'val': None}

        def set_side(val):
            choice['val'] = val
            dlg.destroy()

        tk.Label(dlg, text='Bạn muốn chơi bên nào?').pack(padx=10, pady=10)
        tk.Button(dlg, text='⚪ White', width=14, command=lambda: set_side('white')).pack(pady=4)
        tk.Button(dlg, text='⚫ Black', width=14, command=lambda: set_side('black')).pack(pady=4)
        tk.Button(dlg, text='👥 Both (no AI)', width=14, command=lambda: set_side('both')).pack(pady=4)
        self.master.wait_window(dlg)

        if choice['val']:
            self.human_side = choice['val']
            self.flipped = (self.human_side == 'black')
            self.draw_board(full=False)
            if self.should_ai_move():
                self.request_ai_move()

    def flip_board(self):
        self.flipped = not self.flipped
        self.draw_board(full=True)

    def save_pgn(self):
        game = chess.pgn.Game()
        node = game
        for mv in self.board.move_stack:
            node = node.add_variation(mv)
        pgn_str = str(game)
        fname = filedialog.asksaveasfilename(defaultextension='.pgn', filetypes=[('PGN files','*.pgn')])
        if fname:
            with open(fname, 'w', encoding='utf8') as f:
                f.write(pgn_str)
            messagebox.showinfo('Saved', f'Saved PGN to {fname}')

    def load_pgn(self):
        if self.ai_thinking:
            return
        fname = filedialog.askopenfilename(filetypes=[('PGN files','*.pgn')])
        if not fname:
            return
        try:
            with open(fname, 'r', encoding='utf8') as f:
                game = chess.pgn.read_game(f)
            self.board.reset()
            for mv in game.mainline_moves():
                self.board.push(mv)
            self.draw_board(full=True)
            self.update_move_list(full=True)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load PGN: {e}')

    def on_game_over(self):
        res = 'Game over. '
        if self.board.is_checkmate():
            res += 'Checkmate. '
            res += 'White wins.' if self.board.turn == chess.BLACK else 'Black wins.'
        elif self.board.is_stalemate():
            res += 'Stalemate.'
        elif self.board.is_insufficient_material():
            res += 'Draw by insufficient material.'
        elif self.board.can_claim_draw():
            res += 'Draw (claim available).'
        else:
            res += 'Draw.'
        messagebox.showinfo('Game Over', res)


if __name__ == '__main__':
    root = tk.Tk()
    app = ChessGUI(master=root)
    root.geometry('980x560')
    app.mainloop()
