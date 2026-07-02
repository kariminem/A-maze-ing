## my draft of the class maze generator


class MazeGenerator:
    def __init__(self, width, height, seed, ...):
        self.grid = Grid(width, height)        # 1. Grid erstellen
        forty_two_pattern(self.grid)            # 2. Pattern sperren
        perfect_algo(self.grid, entry_cell)     # 3. Maze generieren