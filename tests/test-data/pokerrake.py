class PokerRake:
    def __init__(self, game):
        self.gotcha = 1

def get_rake_instance(game):
    return PokerRake(game)
