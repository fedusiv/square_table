class GameProcess:
    isRoundBegin = False

    def __init__(self):
       print("Created")


    def process(self):
       if self.isRoundBegin is False:
          # This means that game should start new round
          self.isRoundBegin = True
          



