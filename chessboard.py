class Board:
    def __init__(self):
        """初始化一个10x10的棋盘，所有位置初始为空（用0表示）。"""
        self.board = [[0 for _ in range(10)] for _ in range(10)]
        self.last = ''

    def place(self, x, y, player):
        """在棋盘上放置一个玩家的标记。如果该位置已被占用，则抛出异常。"""
        if self.board[x][y] == 0:
            self.board[x][y] = player
        else:
            raise Exception("Invalid Move: Position already taken.")

    def check(self):
        """检查棋盘上是否有连续五子。返回赢家的标记，如果没有赢家则返回-1。"""
        for i in range(6):
            for j in range(6):
                if self.board[i][j] != 0 and all(self.board[i][j] == self.board[i + k][j] for k in range(5)):
                    return self.board[i][j]
                if self.board[i][j] != 0 and all(self.board[i][j] == self.board[i][j + k] for k in range(5)):
                    return self.board[i][j]
                if self.board[i][j] != 0 and all(self.board[i][j] == self.board[i + k][j + k] for k in range(5)):
                    return self.board[i][j]
        return -1

    def display(self):
        """显示棋盘当前状态。"""
        for row in self.board:
            print(' '.join(str(x) for x in row))

def main():
    game_board = Board()
    while True:
        game_board.display()
        try:
            x, y, player = map(int, input("Enter move (x y player): ").split())
            game_board.place(x, y, player)
            if game_board.check() != -1:
                print(f"Player {player} wins!")
                break
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()
