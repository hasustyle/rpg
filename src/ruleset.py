import random, math
from mcons import *

def GetDmgTypeText(dmgtype):
   if dmgtype == PHYSICAL:
      return "physical"
   else: return ""

class Die:
   def __init__(self, sides=6):
      self.range = (1,sides)
      
   def Roll(self):
      return random.randint(self.range[0], self.range[1])
   
class D6(Die):
   def __init__(self):
      Die.__init__(self, sides=6)
      
class D8(Die):
   def __init__(self):
      Die.__init__(self, sides=8)
      
class D10(Die):
   def __init__(self):
      Die.__init__(self, sides=10)
      
class D12(Die):
   def __init__(self):
      Die.__init__(self, sides=12)
      
class D20(Die):
   def __init__(self):
      Die.__init__(self, sides=20)
      
class D100(Die):
   def __init__(self):
      Die.__init__(self, sides=100)

class RPGRace:
   def __init__(self, name="Unnamed race"):
      self.name = name
      
class RPGProfession:
   def __init__(self, name="Unnamed class"):
      self.name = name

class RPGCreature:
   def __init__(self, name="Unnamed creature", level=1, race=None, prof=None, hp=10):
      self.name = name
      self.level = level
      self.race = race
      self.profession = prof
      
      self.attacks = []
      
      self.movement = 6
      
      self.attributes = { STRENGTH:10, DEXTERITY:10, CONSTITUTION:10, INTELLIGENCE:10,WISDOM:10,CHARISMA:10 }
      
      self.curHp = self.maxHp = hp
      
   def __str__(self):
      return "%s, Lvl %i %s %s" % (self.name, self.level, self.race.name, self.profession.name)
   
   def GetAttributeBonus(self, attrib):
      return math.floor((self.attributes[attrib]-10) / 2)
   
   def GetDodge(self):
      return 10 + self.GetAttributeBonus(DEXTERITY)
   
   def InflictDamage(self, damage):
      out = []
      for dmgComp in damage:
         dmg = sum([die.Roll() for die in dmgComp.dice])
         for bonus in dmgComp.bonuses:
            pass
         out.append("_%s_ suffers _%i_ points of %s damage." % (self.name, dmg, GetDmgTypeText(dmgComp.dmgType)))
         self.curHp -= dmg
      return out
   
   def UseAttack(self, attack, target):
      out = []
      out.append("_%s_ attacks _%s_ with _%s_." % (self.name, target.name, attack.name))
      toHit = D20().Roll()
      if attack.toHit == PHYSICAL:
         hitBonus = self.GetAttributeBonus(STRENGTH)
         defense = target.GetDodge()
      
      hit = toHit+hitBonus >= defense
      out.append("_%i + %i_ to hit vs. dodge _%i_ - _%s_" % (toHit, hitBonus, defense, "hit!" if hit else "miss!"))
      if hit:
         out.extend(target.InflictDamage(attack.damage))
      return out
         
   
class RPGDamage:
   def __init__(self, dice=[D6()], bonuses=[], dmgType=PHYSICAL):
      self.dice = dice
      self.bonuses = bonuses
      self.dmgType = dmgType
   
class RPGAttack:
   def __init__(self, name="Unnamed attack", toHit=PHYSICAL, damage=[RPGDamage()]):
      self.name = name
      self.toHit = toHit
      self.damage = damage