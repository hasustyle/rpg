class RPGRace:
   def __init__(self, name="Unnamed race"):
      self.name = name
      
class RPGProfession:
   def __init__(self, name="Unnamed class"):
      self.name = name

class RPGCreature:
   def __init__(self, name="Unnamed creature", level=1, race=None, prof=None):
      self.name = name
      self.level = level
      self.race = race
      self.profession = prof
      
   def __str__(self):
      return "%s, Lvl %i %s %s" % (self.name, self.level, self.race.name, self.profession.name)