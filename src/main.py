# -*- coding: utf-8 -*-
import pygame, pygame.locals, sys, mcons, math, os, bisect
import ruleset as rs

from ruleset import D6

class MSurface(pygame.Surface):
   def __init__(self, (width, height), flags=0):
      pygame.Surface.__init__(self, (width,height), flags)
   
   def blitAligned(self, source, alignment, margin=0, area=None, special_flags = 0):
      w, h = self.get_width(), self.get_height()
      source_w, source_h = (source.get_width(), source.get_height()) if area is None else (area.width, area.height)
      dx = w - source_w
      dy = h - source_h
      
      if alignment & mcons.LEFT:
         target_x = margin
      elif alignment & mcons.RIGHT:
         target_x = w - (source_w + margin)
      elif alignment & mcons.HCENTER:
         target_x = dx // 2
         
      if alignment & mcons.TOP:
         target_y = margin
      elif alignment & mcons.BOTTOM:
         target_y = h - (source_h + margin)
      elif alignment & mcons.VCENTER:
         target_y = dy // 2
         
      return self.blit(source, (target_x, target_y), area, special_flags)

class Theme:
   def __init__( self ):
      pygame.font.init()
      
      self.fontSize = 12
      self.bgColor = pygame.Color( 0, 0, 0, 170 )
      self.textColor = pygame.Color( 170, 170, 100 )
      self.highlightColor = pygame.Color( 230, 230, 90 )
      self.borderColor = pygame.Color( 150, 150, 40 )
      self.darkBorderColor = pygame.Color( 20, 20, 20 )
      
      self.popFont = pygame.font.Font(os.path.join("fonts","segoeb.ttf"), 26)
      self.popFontBig = pygame.font.Font(os.path.join("fonts","segoeb.ttf"), 30)
      
      self.font = pygame.font.Font(pygame.font.get_default_font(), self.fontSize)
      self.boldFont = pygame.font.Font(pygame.font.get_default_font(), self.fontSize)
      self.boldFont.set_bold(True)
      #self.font = pygame.font.Font("DejaVuSans.ttf", self.fontSize)
      #self.boldFont = pygame.font.Font("DejaVuSansBold.ttf", self.fontSize)
      self.spacing = 2
      
class Interface:
   def __init__( self, theme=Theme() ):
      self.theme = theme
      
   def AttackTooltip( self, attack ):
      headline = self.theme.boldFont.render( attack.name, True, self.theme.highlightColor )
      descText = "+%i vs. %s, %s damage" % ( attack.fixedAtkBonus, attack.defense, "%s+%i" % ( attack.dmgDice.Str(), attack.fixedDmgBonus  ) )
      desc = self.theme.font.render( descText, True, self.theme.textColor )
      
      w = max( headline.get_width(), desc.get_width() )
      h = headline.get_height() + desc.get_height()
      surf = pygame.Surface((w, h), pygame.SRCALPHA)
      surf.fill( self.theme.bgColor )
      surf.blit( headline, (0,0) )
      surf.blit( desc, (0, headline.get_height() + self.theme.spacing) )
      
      return self.Box(surf)
   
   def DamagePopup( self, damage ):
      back = self.theme.popFontBig.render( str(damage), True, self.theme.darkBorderColor )
      front = self.theme.popFont.render( str(damage), True, self.theme.highlightColor )
      
      offset = ((back.get_width() - front.get_width())//2, (back.get_height() - front.get_height())//2)
      back.blit( front, offset )
      return back
   
   def InitGfx( self, rcLib ):
      invGfx = ("InvMainhand", "InvOffhand", "InvHead", "InvNeck", "InvShoulder", "InvBack", "InvChest", "InvWrist", \
                "InvHands", "InvWaist", "InvLegs", "InvFeet", "InvFinger", "InvFinger")
      
      w,h = 0,0
      for slot in invGfx:
         icon = rcLib.GetIcon(slot.lower())
         if icon is None: print slot
         h += icon.get_width()
         if icon.get_height() > w: w = icon.get_height()
         
      w += 5*rcLib.GetIcon("invbag").get_width()
         
      invSurf = pygame.Surface((w,h))
      y = 0
      for slot in invGfx:
         invSurf.blit( rcLib.GetIcon(slot.lower()), (0,y) )
         for i in range(5):
            invSurf.blit( rcLib.GetIcon("invbag"), ((i+1)*rcLib.GetIcon("invbag").get_width(), y))
         y += rcLib.GetIcon(slot.lower()).get_width()
         
      self.inventorySurface = invSurf
   
   def CreatureTooltip(self, creature, showHp = False):
      headline = self.theme.boldFont.render( creature.profile.name, True, self.theme.highlightColor )
      hpPerc = max(0., 1. * creature.profile.curHp / creature.profile.maxHp)
      
      if showHp:
         descText = "%i" % creature.profile.curHp
      
      else:
         if hpPerc == 1.:
            descText = "Uninjured"
         elif 0.7 < hpPerc < 1.:
            descText = "Barely injured"
         elif 0.5 < hpPerc <= 0.7:
            descText = "Injured"
         elif 0.25 < hpPerc <= 0.5:
            descText = "Badly injured"
         elif 0. < hpPerc <= 0.25:
            descText = "Near death"
         else:
            descText = "Dead"
      
      color = (min(255, (1.-hpPerc)*510), min(255, hpPerc*510), 0)
      curHpText = self.theme.font.render( descText, True, color )
      
      if showHp:
         maxHpText = self.theme.font.render(" / %i" % creature.profile.maxHp, True, self.theme.textColor)
         w = max( headline.get_width(), curHpText.get_width()+maxHpText.get_width() )
         h = headline.get_height() + max(curHpText.get_height(), maxHpText.get_height())
      else:
         w = max( headline.get_width(), curHpText.get_width() )
         h = headline.get_height() + curHpText.get_height()
         
      surf = pygame.Surface((w, h), pygame.SRCALPHA)
      #surf.fill( self.theme.bgColor )
      surf.blit( headline, (0,0) )
      surf.blit( curHpText, (0, headline.get_height() + self.theme.spacing) )
      if showHp:
         surf.blit( maxHpText, (curHpText.get_width(), max(curHpText.get_height(), maxHpText.get_height()) + self.theme.spacing))
      
      return Sprite.FromSurface(self.Box(surf))

   def Box( self, surf, width=None, height=None ):
      if width is None: width = surf.get_width() + 2*(self.theme.spacing+2)
      if height is None: height = surf.get_height() + 2*(self.theme.spacing+2)
      
      s = pygame.Surface((width,height), pygame.SRCALPHA)
      s.fill( self.theme.borderColor )
      s.fill( self.theme.bgColor, s.get_rect().inflate(-2,-2))
      s.blit( surf, (2+self.theme.spacing, 2+self.theme.spacing))
      
      return s
   
   def RenderText(self, text):
      if len(text) == 0: return pygame.Surface((1, 1), pygame.SRCALPHA)
      lines = text.splitlines()
      lineSurfs = []
      
      for line in lines:
         surfs = []
         highlight = False
         words = line.split("_")
         for w in words:
            if not highlight and len(w)>0:
               surfs.append( self.theme.font.render(w, True, self.theme.textColor) )
            elif len(w)>0:
               surfs.append( self.theme.font.render(w, True, self.theme.highlightColor) )
            highlight = not highlight
            
         width = 0
         for s in surfs:
            width += s.get_width()
            
         ls = pygame.Surface((width, surfs[0].get_height()), pygame.SRCALPHA)
         x = 0
         for s in surfs:
            ls.blit( s, (x, 0) )
            x += s.get_width()
         
         lineSurfs.append(ls)
      
      width = 0
      height = - self.theme.spacing
      for ls in lineSurfs:
         if ls.get_width() > width: width = ls.get_width()
         height += ls.get_height() + self.theme.spacing
         
      surf = pygame.Surface((width, height), pygame.SRCALPHA)
      #surf.fill( self.theme.bgColor )
      y = 0
      for ls in lineSurfs:
         surf.blit( ls, (0, y) )
         y += ls.get_height() + self.theme.spacing
         
      return surf
   
class LogWidget:
   scrollStep = 12
   
   def __init__(self, width=600, height=100, interface=Interface()):
      self.interface = interface
      self.entries = []
      self.sprite = Sprite(width, height, z=20, offset=False)
      self.sprite.image = self.interface.Box(self.interface.RenderText("\n".join(self.entries)), self.sprite.rect.w, self.sprite.rect.h)
      
      self.scrollPos = 0 # current scroll position
      self.totalHeight = 0 # total height of all text
      
      self.theme = Theme()
      self.Update()
      
   def ProcessEvents(self, events):
      ignoredEvents = []
      
      for e in events:
         if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.Export()
         else:
            ignoredEvents.append(e)
      
      return ignoredEvents
   
   def Export(self):
      filename = "combatlog.txt"
      with open(filename, "w") as f:
         f.write("Combat log export dd.mm.yyyy - hh:mm\r\n\r\n")
         f.write("\r\n".join(self.entries))
         
      os.system("start " + filename)
      
   def ScrollUp(self):
      self.scrollPos -= LogWidget.scrollStep
      if self.scrollPos < 0: self.scrollPos = 0
      self.Update()
      
   def ScrollDown(self):
      h = self.sprite.rect.h - 2*(self.theme.spacing+2)
      self.scrollPos += LogWidget.scrollStep
      if self.scrollPos > self.totalHeight - h: self.scrollPos = max(0, self.totalHeight - h)
      self.Update()
      
   def ScrollToBottom(self):
      h = self.sprite.rect.h - 2*(self.theme.spacing+2)
      self.scrollPos = max(0, self.totalHeight - h)
      self.Update()
      
   def Log(self, text):
      self.entries.append(text)
      self.Update()
      self.ScrollToBottom()
   
   def GetSprite(self):
      return self.sprite
   
   def Update(self):
      textSurf = self.interface.RenderText("\n".join(self.entries))
      self.totalHeight = textSurf.get_rect().h
      
      w, h = self.sprite.rect.w - 2*(self.theme.spacing+2), self.sprite.rect.h - 2*(self.theme.spacing+2)
      
      croppedTextSurf = pygame.Surface((w,h), pygame.SRCALPHA)
      croppedTextSurf.blit(textSurf, (0,0), area=croppedTextSurf.get_rect().move(0,self.scrollPos))
      self.sprite.image = self.interface.Box(croppedTextSurf, self.sprite.rect.w, self.sprite.rect.h)
      
      visiblePart = [1.*self.scrollPos/self.totalHeight, min(1., 1.*(self.scrollPos+h)/self.totalHeight)]
      scrollBarHeight = self.sprite.rect.h * (visiblePart[1] - visiblePart[0])
      scrollBarY = self.sprite.rect.h * visiblePart[0]
      self.sprite.image.blit( self.interface.Box(pygame.Surface((1,1), pygame.SRCALPHA), width=4, height=scrollBarHeight), (self.sprite.rect.w - 4, scrollBarY) )
      
class Popup:
   speed = 70.
   
   def __init__(self, surf, position):
      self.sprite = Sprite.FromSurface(surf, position)
      self.lifetime = 1.
      self.dead = False
      self.offset = 0.
      self.origY = position[1]
      
   def Move(self, time):
      self.lifetime -= 1. * time / 1000.
      if self.lifetime <= 0.:
         self.dead = True
         self.sprite.visible = False
      
      self.offset += Popup.speed * time / 1000.
      self.sprite.rect.top = self.origY - self.offset

class Screen:
   def __init__(self, width, height, caption="Untitled window"):
      self.width = width
      self.height = height
      self.surface = pygame.display.set_mode((width, height))
      pygame.display.set_caption(caption)
      
   def Update(self):
      pygame.display.update()

class EventHandler:
   def __init__(self):
      self.events = []
      self.pressedKeys = []

   def GetEvents(self):
      self.events.extend(pygame.event.get())
      
   def ProcessEvents(self):
      ignoredEvents = []
      
      while len(self.events) > 0:
         e = self.events.pop(0)
         if e.type == pygame.locals.QUIT or \
           (e.type == pygame.locals.KEYDOWN and e.key == pygame.locals.K_ESCAPE):
            pygame.quit()
            sys.exit()
         else:
            if e.type == pygame.locals.KEYDOWN:
               self.pressedKeys.append(e.key)
            elif e.type == pygame.locals.KEYUP and e.key in self.pressedKeys:
               self.pressedKeys.remove(e.key)
            ignoredEvents.append(e)
      
      return ignoredEvents

class Scene(EventHandler):
   def __init__(self, sizeX=1024, sizeY=768):
      EventHandler.__init__(self)
      self.sprites = SpriteGroup()
      self.flags = 0
      self.nextScene = None
      self.screenSize = (sizeX,  sizeY)
   
   def Align(self, sprite, alignment):
      """ Align a sprite's position to a given position on the screen. """
      w, h = sprite.rect.w, sprite.rect.h
      
      if alignment & mcons.TOP:  sprite.rect.top = 0
      elif alignment & mcons.BOTTOM: sprite.rect.bottom = self.screenSize[1]
      elif alignment & mcons.VCENTER: sprite.rect.centery = self.screenSize[1] // 2
      
      if alignment & mcons.LEFT: sprite.rect.left = 0
      elif alignment & mcons.RIGHT: sprite.rect.right = self.screenSize[0]
      elif alignment & mcons.HCENTER: sprite.rect.centerx = self.screenSize[0] // 2
   
   def Frame(self):
      pass
      
   def Render(self, surface):
      self.sprites.draw(surface)
#      for sprite in self.sprites:
#         sprite.Draw(surface)
#      self.eventHandler = EventHandler()
#       
#       self.sprites.append(Sprite(self.screenSize[0],self.screenSize[1]))
#       
#    def SetBackground(self, color):
#       self.sprites[0].image.fill(color)

class Creature:
   NoIcon = pygame.image.load(os.path.join('gfx', 'noicon.png'))
   
   def __init__(self, sprite=None):
      self.sprites = {mcons.DEFAULT:sprite}
      self.state = mcons.DEFAULT
      
      self.pos = [0., 0.] if sprite is None else [1.*sprite.rect.centerx, 1.*sprite.rect.centery]
      self.tile = None
      self.path = []
      
      self.profile = rs.RPGCreature("Alrik", 1, rs.RPGRace("Human"), rs.RPGProfession("Warrior"), hp=12)
      self.movementLeft = self.profile.movement
      self.icon = Creature.NoIcon
      self.initiative = 1.
      
   def InitRound(self):
      self.movementLeft = self.profile.movement
      
   def GetSprite(self):
      return self.sprites[self.state] if self.state in self.sprites else self.sprites[mcons.DEFAULT]
   
#   def GetTooltip(self):
#      return Tooltip(str(self.profile))

class InitiativeManager:
   def __init__(self, width=600, interface=Interface()):
      self.creatures = []
      self.timelineSprite = None
      self.dirty = True
      self.width = width
      
      self.interface = interface
      
      self.rects = [] # contains (rect,creature) tuples with rect being a creature's icon rect in timeline
      
   def GetTimelineSprite(self):
      if self.timelineSprite is not None and not self.dirty:
         return self.timelineSprite
      
      hIcon = 48
      hEff = hIcon + 2*(self.interface.theme.spacing+2)
      
      self.dirty = False
      
      if len(self.creatures) > 0:
         minIni = self.creatures[0].initiative
         maxIni = self.creatures[-1].initiative
         
         dt = maxIni-minIni
         if dt <= 1.e-12: dt = 1. 
      
      effwidth = self.width - hEff
      
      if not self.timelineSprite:
         self.timelineSprite = Sprite(self.width, hEff, z=20, offset=False)
         
      self.timelineSprite.image = MSurface((self.width, hEff), pygame.SRCALPHA)
      
      self.rects = []
      for cre in reversed(self.creatures): # reverse to draw 'quicker' icons on top of slower ones.
         x = cre.initiative / dt * effwidth
         img = self.interface.Box(cre.icon)
         self.timelineSprite.image.blit(img, (x,0))
         
         self.rects.append((img.get_rect().move(x,0),cre))
      
      self.dirty = False
      return self.timelineSprite
   
   def HoveredCreature(self, mousepos):
      hits = []
      for rect, cre in self.rects:
         if rect.collidepoint(mousepos): hits.append(cre)
         
      hits = sorted(hits, key=lambda cre: cre.initiative)
      if len(hits)>0:
         return hits[0]
      return None
      
   def InsertCreature(self, creature):
      self.dirty = True
      
      # insert manually to correct position, bisection is of no use here as the list
      # can only be traversed with linear cost anyway.
      i=0
      inserted = False
      for cre in self.creatures:
         if cre.initiative > creature.initiative:    # if a creature has higher initiative
            self.creatures.insert(i, creature)       # insert the former active creature right before it
            break
         i+=1
      if not inserted: self.creatures.append(creature)
   
   def Next(self, dt):
      """ Call when currently active creature has acted with a duration worth 'dt' initiative.
        That creature is then removed from the top of the list, inserted back to it's new order
        and time will be advanced so that the next creature in order may act.
        This creature is then returned. """
      self.dirty = True
      
      active = self.creatures.pop(0)
      active.initiative += dt
      
      self.InsertCreature(active)
      
      # "normalize" initiative, so that the first creature has ini 0 and can act right now.
      for cre in self.creatures:
         cre.initiative -= self.creatures[0].initiative
         
      return self.creatures[0]
         
   def Update(self):
      self.creatures = sorted(self.creatures, key=lambda cre:cre.initiative)
      self.dirty = True
      self.GetTimelineSprite()

class CombatScene(Scene):
   ScrollKeys = (pygame.locals.K_UP, pygame.locals.K_DOWN, pygame.locals.K_LEFT, pygame.locals.K_RIGHT)
   
   def __init__(self, backgroundImg=""):
      Scene.__init__(self)
      
      # initial parameters
      self.mapSizeX, self.mapSizeY = (21.,21.)                                # map size in meters/physical length unit
      self.ppm = 48.                                                          # zoom factor / pixels per meter
      self.tileSize = 1.5                                                     # tile size in meters/physical length
      self.scrollSpeed = 0.13                                                 # scroll length per frame
      self.movementSpeed = 6.                                                 # movement length per frame
      
      self.cameraX, self.cameraY = (0.,0.)                                    # top left corner of initial camera
      
      self.gridColor = (20,180,250,200)                                       # grid colors
      self.gridBgA = (12,108,150,100)                                         # checkerboard grid background color 1
      self.gridBgB = (8,72,100,100)                                           # checkerboard grid background color 2
      
      # initial flags
      self.scrolling = False
      self.movingCreature = False
      self.showGrid = False
      self.showActiveTile = True
      
      self.tooltip = None
      
      
      # child objects
      self.interface = Interface()                                            # use default interface
      self.logWidget = LogWidget(interface=self.interface)
      self.iniMgr = InitiativeManager()
      
      self.Align(self.logWidget.GetSprite(), mcons.TOPRIGHT)
      self.Align(self.iniMgr.GetTimelineSprite(), mcons.BOTTOMCENTER)
      
      self.sprites.add(self.logWidget.GetSprite())
      self.sprites.add(self.iniMgr.GetTimelineSprite())
      
      
      
      # variables
      self._roundNum = 0
      
      
      
      # contained lists of objects      
      self.creatures = []
      self.selectedCreature = None
      self.movingCreatures = []
      self.hlTileSprites = []
      self.highlightedTiles = []
      
      srs = 0.1 # scroll rect size, percentage of screen width/height in which to scroll by mouse
      w, h = self.screenSize
      self.scrollRects = {
            mcons.SCROLL_UP:    pygame.Rect(0,0,w,h*srs),
            mcons.SCROLL_DOWN:  pygame.Rect(0,h*(1.-srs),w,h*srs),
            mcons.SCROLL_LEFT:  pygame.Rect(0,0,w*srs,h),
            mcons.SCROLL_RIGHT: pygame.Rect(w*(1.-srs),0,w*srs,h)}
      
      if mcons.DEBUG:
         self.mapArea = Sprite(self.mapSizeX*self.ppm, self.mapSizeY*self.ppm)
         self.mapArea.image.fill((40,150,150))
         self.sprites.add(self.mapArea)
      
      self.background = Sprite(self.mapSizeX*self.ppm, self.mapSizeY*self.ppm, z=0)
      if backgroundImg != "":
         self.background.image.blit(pygame.image.load(os.path.join("gfx",backgroundImg)).convert(), (0,0))
      self.sprites.add(self.background)
      
      # initialize image for highlighted tiles (e.g. tiles you are able to move to)
      tileSpacing = 0 # currently bugged if greater than 0
      spacedSize = self.tileSize * self.ppm - (tileSpacing*2)
      fullSize = self.tileSize * self.ppm
      
      self.hlTileImage = pygame.Surface((self.tileSize*self.ppm, self.tileSize*self.ppm), pygame.SRCALPHA)
      self.hlTileImage.fill(pygame.Color(12,108,150,100))
      pygame.draw.rect(self.hlTileImage, self.gridColor, (tileSpacing, tileSpacing, spacedSize, spacedSize), 1) # tile border
      
      self.grid = Sprite(self.mapSizeX*self.ppm, self.mapSizeY*self.ppm, z=2)
      self.grid.image.fill(pygame.Color(0,0,0,0))
      self.grid.image = self.grid.image.convert_alpha()
      for i in range(int(self.mapSizeX//self.tileSize)):
         for j in range(int(self.mapSizeY//self.tileSize)):
            color = self.gridBgA if (i+j%2)%2 == 0 else self.gridBgB
            pygame.draw.rect(self.grid.image, color, (i*self.tileSize*self.ppm+tileSpacing, j*self.tileSize*self.ppm+tileSpacing, spacedSize, spacedSize)) # tile background
            pygame.draw.rect(self.grid.image, self.gridColor, (i*self.tileSize*self.ppm+tileSpacing, j*self.tileSize*self.ppm+tileSpacing, spacedSize, spacedSize), 1) # tile border
      self.sprites.add(self.grid)
      
      self.hoveredTileSprite = Sprite(fullSize, fullSize, z=4)
      self.hoveredTileSprite.image = self.hoveredTileSprite.image.convert_alpha()
      pygame.draw.rect(self.hoveredTileSprite.image, (0,0,0,0), (0,0,self.tileSize * self.ppm,self.tileSize * self.ppm))
      pygame.draw.rect(self.hoveredTileSprite.image, (255,255,255), (0,0,self.tileSize * self.ppm,self.tileSize * self.ppm), 1)
      self.sprites.add(self.hoveredTileSprite)
      
      self.InitTiles()
      
      self.AddCreature(Creature(Sprite.FromSurface(pygame.image.load(os.path.join("gfx","hero.png")).convert())), (0,0))
      self.creatures[0].profile.name = "Geron"
      self.AddCreature(Creature(Sprite.FromSurface(pygame.image.load(os.path.join("gfx","hero.png")).convert())), (3,4))
      
      self.creatures[0].initiative = 1.
      self.creatures[1].initiative = 0.
      
      #self.MoveCreatureToTile(self.creatures[1], self.tiles[0][0])
      #self.MoveCreatureToTile(self.creatures[1], self.tiles[3][4])
      
      #self.SetActiveCreature(self.creatures[1])
      self.BeginActivation(self.creatures[1])
      
      jabDagger = rs.RPGAttack("Jab (Dagger)", mcons.PHYSICAL, [rs.RPGDamage([D6()], bonuses = [mcons.DEXTERITY])] )
      self.selectedCreature.profile.attacks.append(jabDagger)
      
   def AddCreature(self, creature, position):
      self.creatures.append(creature)
      self.iniMgr.InsertCreature(creature)
      self.MoveCreatureToTile(creature, self.tiles[position[0]][position[1]], anim=False, checkDist=False)
      
   def AdjacentTiles(self, tile):
      x, y = tile.x, tile.y
      
      adj = []
      for pos in ((x-1,y-1), (x-1,y), (x-1,y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)):
         if 0 <= pos[1] and pos[1] < len(self.tiles) and 0 <= pos[0] and pos[0] < len(self.tiles[pos[1]]):
            adj.append(self.tiles[pos[0]][pos[1]])
      return adj
   
   def EndActivation(self, dt=1.5):
      #self._roundNum += 1
      self.BeginActivation(self.iniMgr.Next(dt))
      
   def BeginActivation(self, creature):
      self.logWidget.Log("It's _%s's_ turn." % creature.profile.name)
      creature.InitRound()
      self.SetActiveCreature(creature)
      
   def SetActiveCreature(self, creature):
      self.selectedCreature = creature
      self.iniMgr.Update()
      self.UpdateHighlightedTiles()
      
   def Frame(self):
      dx, dy = 0., 0.
      
      mouseScrolling = False
      if self.scrollRects[mcons.SCROLL_UP].collidepoint(pygame.mouse.get_pos()):
         dy -= 1.
         mouseScrolling = True
      if self.scrollRects[mcons.SCROLL_DOWN].collidepoint(pygame.mouse.get_pos()):
         dy += 1.
         mouseScrolling = True
      if self.scrollRects[mcons.SCROLL_LEFT].collidepoint(pygame.mouse.get_pos()):
         dx -= 1.
         mouseScrolling = True
      if self.scrollRects[mcons.SCROLL_RIGHT].collidepoint(pygame.mouse.get_pos()):
         dx += 1.
         mouseScrolling = True
      self.MoveCamera(self.scrollSpeed*dx, self.scrollSpeed*dy)
      
      if self.scrolling:
         dx, dy = 0., 0.
         if pygame.locals.K_UP in self.pressedKeys: dy -= 1.
         if pygame.locals.K_DOWN in self.pressedKeys: dy += 1.
         if pygame.locals.K_LEFT in self.pressedKeys: dx -= 1.
         if pygame.locals.K_RIGHT in self.pressedKeys: dx += 1.
         self.MoveCamera(self.scrollSpeed*dx, self.scrollSpeed*dy)
      
      if self.movingCreature:
         for cre in self.movingCreatures:
            target = cre.movTarget #pygame.mouse.get_pos()[0]+self.cameraX*self.ppm, pygame.mouse.get_pos()[1]+self.cameraY*self.ppm
            curpos = cre.pos
         
            dx = 1. * target[0] - curpos[0]
            dy = 1. * target[1] - curpos[1]
            dist2 = dx**2+dy**2
            if dist2 <= 1.:
               cre.path.pop(0)
               if len(cre.path) > 0:
                  cre.movTarget = cre.path[0]
               else:
                  cre.movTarget = None
                  self.movingCreatures.remove(cre)
                  if cre == self.selectedCreature: self.UpdateHighlightedTiles()
                  if len(self.movingCreatures) == 0: self.movingCreature = False
               
            else:
               angle = math.atan2(dy, dx)
               move_r = min( self.movementSpeed, math.sqrt(dist2) )
         
               self.MoveCreature(cre, move_r*math.cos(angle),move_r*math.sin(angle))
               
      if self.scrolling or mouseScrolling or self.movingCreature:
         self.UpdateTooltip()
         
      self.grid.visible = self.showGrid
      self.hoveredTileSprite.visible = (self.HoveredTile() is not None and self.showActiveTile)
         
   def InitTiles(self):
      self.tiles = []
      for i in range(int(self.mapSizeX//self.tileSize)):
         row = []
         for j in range(int(self.mapSizeY//self.tileSize)):
            row.append(Tile(i,j,self.tileSize*self.ppm))
         self.tiles.append(row)
         
   def HoveredTile(self):
      mousepos = pygame.mouse.get_pos()[0]+self.cameraX*self.ppm, pygame.mouse.get_pos()[1]+self.cameraY*self.ppm
      i = int(mousepos[0] // (self.tileSize*self.ppm))
      j = int(mousepos[1] // (self.tileSize*self.ppm))
      if 0 <= i and i < len(self.tiles) and 0 <= j and j < len(self.tiles[i]):
         return self.tiles[i][j]
      else: return None
      
   def MoveCamera(self, dx, dy):
      self.cameraX = min( max( self.cameraX+dx, -1 ), self.mapSizeX + 1 -self.screenSize[0]/self.ppm )
      self.cameraY = min( max( self.cameraY+dy, -1 ), self.mapSizeY + 1 -self.screenSize[1]/self.ppm )
      
   def MoveCreature(self, creature, dx, dy):
      creature.pos[0] += dx
      creature.pos[1] += dy
      
      creature.GetSprite().rect.center = (creature.pos[0],creature.pos[1])
      
   def MoveCreatureToTile(self, creature, tile, anim=False, checkDist=False):
      if not creature.tile:
         dist = 0
      else:
         dist = max(abs(creature.tile.x - tile.x), abs(creature.tile.y - tile.y))
         if checkDist and dist > creature.movementLeft: return
      
      creature.tile = tile
      creature.movementLeft = max( creature.movementLeft - dist, 0 )
      
      # if already moving, just change the target and continue animation
      if creature in self.movingCreatures:
         creature.movTarget = tile.rect.center
         creature.path[0] = tile.rect.center
      
      # otherwise, issue new movement if animation is desired, else just set new position      
      else:
         if anim:
            creature.movTarget = tile.rect.center
            creature.path.insert(0,tile.rect.center)
            self.movingCreatures.append(creature)
            self.movingCreature = True
         else:
            creature.GetSprite().rect.center = tile.rect.center
            creature.pos = [tile.rect.centerx, tile.rect.centery]
      
      self.UpdateHighlightedTiles()
      
   def ProcessEvents(self):
      events = EventHandler.ProcessEvents(self)
      mousepos = pygame.mouse.get_pos()[0]+self.cameraX*self.ppm, pygame.mouse.get_pos()[1]+self.cameraY*self.ppm
      hoveredTile = self.HoveredTile()
      
      for e in events:
         if e.type == pygame.locals.KEYDOWN:
            if e.key in CombatScene.ScrollKeys:
               self.scrolling = True
            
            elif e.key == pygame.locals.K_g:
               self.showGrid = not self.showGrid 
            
            elif e.key == pygame.locals.K_h:
               self.showActiveTile = not self.showActiveTile
               
            elif e.key == pygame.locals.K_RETURN:
               self.EndActivation()
               
         elif e.type == pygame.locals.KEYUP:
            if e.key in CombatScene.ScrollKeys:
               noScroll=True
               for key in CombatScene.ScrollKeys:
                  if key in self.pressedKeys:
                     noScroll=False
                     break
               if noScroll: self.scrolling = False
               
         elif e.type == pygame.locals.MOUSEMOTION:
            # e.buttons is a (p1,p2,p3) tuple where p1, p2, p3 are 0 or 1 depending on if the corresponding button is pressed
            # mouse motion with Button 3 pressed? move camera!
            if e.buttons[1]:
               self.MoveCamera(-e.rel[0]/self.ppm, -e.rel[1]/self.ppm)
            
            if hoveredTile:
               self.hoveredTileSprite.rect = hoveredTile.rect
               
            self.UpdateTooltip()
                  
               
         elif e.type == pygame.MOUSEBUTTONDOWN:
            if self.logWidget.sprite.rect.collidepoint(pygame.mouse.get_pos()):
               ignoredEvents = self.logWidget.ProcessEvents([e]) 
               if e not in ignoredEvents: continue 
            
            if e.button == 1:
               if hoveredTile:
                  # check if a different creature is hovered
                  hoveredCreature = None
                  for cre in self.creatures:
                     if cre.GetSprite().rect.collidepoint(mousepos):
                        hoveredCreature = cre
                        break
                  
                  if hoveredCreature and hoveredCreature != self.selectedCreature: # attack
                     o = self.selectedCreature.profile.UseAttack(self.selectedCreature.profile.attacks[0], hoveredCreature.profile)
                     for s in o: self.logWidget.Log(s)
                  else: # move
                     self.MoveCreatureToTile(self.selectedCreature, hoveredTile, anim=True, checkDist=True)
            elif e.button == 4:
               self.logWidget.ScrollUp()
            elif e.button == 5:
               self.logWidget.ScrollDown()
               
         elif e.type == pygame.MOUSEBUTTONUP:
            pass
            #if e.button == 1:
            #   self.movingCreature=False
      
   def Render(self, surface):
      surface.fill((0,0,0)) # draw black background because the screen might be larger than the combat area
       
      self.sprites.draw(surface, (-self.cameraX*self.ppm, -self.cameraY*self.ppm))
       
       #for sprite in self.sprites:
         #if sprite.visible: surface.blit(sprite.image, sprite.rect.move(-self.cameraX*self.ppm, -self.cameraY*self.ppm))
         #sprite.Draw(surface, sprite.rect.move(-self.cameraX*self.ppm, -self.cameraY*self.ppm))

      #for tile in self.highlightedTiles:
      #   surface.fill((12,108,150,100), tile.rect.move(-self.cameraX*self.ppm, -self.cameraY*self.ppm))
         
      for creature in self.creatures:
         spr = creature.GetSprite() 
         spr.Draw(surface, spr.rect.move(-self.cameraX*self.ppm, -self.cameraY*self.ppm))
         
      if self.tooltip:
         self.tooltip.rect.bottomleft = pygame.mouse.get_pos() 
         self.tooltip.Draw(surface)
         
      #self.iniMgr.Update()
      #self.iniMgr.GetTimelineSprite().Draw(surface)
         
      #self.logWidget.GetSprite().Draw(surface)
         
   def UpdateTooltip(self):
      mousepos = pygame.mouse.get_pos()[0]+self.cameraX*self.ppm, pygame.mouse.get_pos()[1]+self.cameraY*self.ppm
      
      self.tooltip = None
      
      # check if a creature is hovered
      for creature in self.creatures:
         if creature.GetSprite().rect.collidepoint(mousepos):
            self.tooltip = self.interface.CreatureTooltip(creature, showHp=True)
            return
         
      # check if a creature icon in iniMgr timeline is hovered
      if self.iniMgr.GetTimelineSprite().rect.collidepoint(pygame.mouse.get_pos()):
         #print self.iniMgr.GetTimelineSprite().rect
         innerMousePos = pygame.mouse.get_pos()[0] - self.iniMgr.GetTimelineSprite().rect.left, \
                         pygame.mouse.get_pos()[1] - self.iniMgr.GetTimelineSprite().rect.top
         
         #print innerMousePos
         hov = self.iniMgr.HoveredCreature(innerMousePos)
         if hov is not None:
            self.tooltip = self.interface.CreatureTooltip(hov, showHp=True)
         
         
   def UpdateHighlightedTiles(self):
      [self.sprites.remove(s) for s in self.hlTileSprites]
      self.hlTileSprites = []
      self.highlightedTiles = []
      
      if not self.selectedCreature \
         or self.selectedCreature.tile is None \
         or self.selectedCreature in self.movingCreatures \
         or self.selectedCreature.movementLeft == 0: return
      
      hlset = set()
      hlset.add(self.selectedCreature.tile)
      for i in range(self.selectedCreature.movementLeft):
         newhlset = hlset.copy()
         for tile in hlset:
            [newhlset.add(t) for t in self.AdjacentTiles(tile)]
         hlset = newhlset
         
      for tile in hlset:
         self.highlightedTiles.append(tile)
         spr = Sprite.FromSurface(self.hlTileImage, tile.rect.topleft)
         spr.z = 1
         self.hlTileSprites.append(spr)
         self.sprites.add(spr)
      
         
class MenuScene(Scene):
   def __init__(self):
      Scene.__init__(self)
      
      self.menuItems = [] 
      self.selectedItem = -1
      
      self.wrapCursor = True
      self.highlightMode = mcons.SELECTOR
      self.selector = Sprite(10, 16)
      self.selector.visible = False
      self.selectorMargin = 10
      self.autoSelect = True # automatically select the first menu item when creating the menu
      pygame.draw.polygon(self.selector.image, (240,230,170), ((0,0),(10,8),(0,16)))
      
      self.itemAlignment = mcons.HCENTER
      self.itemSpacing = 30
      self.selectionMode = mcons.KEYBOARD
      
      self.backgroundColor = (0,0,0)
      
      self.background = Sprite(self.screenSize[0],self.screenSize[1])
      self.background.image.fill(self.backgroundColor)
      self.sprites.add(self.background)

   def AddItem(self, item, x=-1, y=-1):
      """ Adds a sprite as a menu item and tries to position it automatically, by placing it beneath the
         last item. Positionig can be manually overwritten."""
      if y < 0 and len(self.menuItems) > 0:
         iy = self.menuItems[-1].rect.bottom + self.itemSpacing
      elif y < 0:
         iy = 3*self.itemSpacing
      else: #manual placement
         iy = y
      
      if x < 0 and len(self.menuItems) > 0:
         if self.itemAlignment & mcons.LEFT:
            ix = self.menuItems[-1].rect.left
         elif self.itemAlignment & mcons.RIGHT:
            ix = self.menuItems[-1].rect.right - item.rect.width
         elif self.itemAlignment & mcons.HCENTER:
            ix = self.menuItems[-1].rect.centerx - math.floor(0.5*item.rect.width)
      elif x < 0:
         if self.itemAlignment & mcons.LEFT:
            ix = 5*self.itemSpacing
         elif self.itemAlignment & mcons.RIGHT:
            ix = self.screenSize[1] - 5*self.itemSpacing - item.rect.width
         elif self.itemAlignment & mcons.HCENTER:
            ix = math.floor(0.5*(self.screenSize[0]-item.rect.width))
      else: #manual placement
         ix = x
         
      item.rect.topleft = (ix, iy)
      
      self.menuItems.append(item)
      self.sprites.add(item)
      
      if self.autoSelect and self.selectedItem < 0:
         self.selectedItem = 0
         self.UpdateSelection()
   
   def MoveDown(self):
      if len(self.menuItems)==0: return
      
      if self.selectedItem < 0:
         self.selectedItem = 0
      elif self.selectedItem < len(self.menuItems)-1:
         self.selectedItem += 1
      elif self.selectedItem == len(self.menuItems)-1 and self.wrapCursor:
         self.selectedItem = 0
         
      self.UpdateSelection()
      
   def MoveUp(self):
      if len(self.menuItems)==0: return
      
      if self.selectedItem > 0:
         self.selectedItem -= 1
      elif self.selectedItem == 0:
         self.selectedItem = len(self.menuItems) - 1
      elif self.selectedItem < 0 and self.wrapCursor:
         self.selectedItem = 0
         
      self.UpdateSelection()
      
   def ItemTriggered(self, item):
      raise NotImplementedError("Virtual method ItemTriggered called in abstract class MenuScene. Please reimplement in a subclass to use!")
      
   def ProcessEvents(self):
      events = EventHandler.ProcessEvents(self)
      
      for e in events:
         if e.type == pygame.locals.KEYDOWN:
            if e.key == pygame.locals.K_UP:
               self.MoveUp()
               self.selectionMode = mcons.KEYBOARD
            elif e.key == pygame.locals.K_DOWN:
               self.MoveDown()
               self.selectionMode = mcons.KEYBOARD
            elif e.key == pygame.locals.K_RETURN and self.selectedItem >= 0:
               self.ItemTriggered(self.selectedItem)
               self.selectionMode = mcons.KEYBOARD
               
         elif e.type == pygame.locals.MOUSEMOTION:
            # check if an item is hovered
            i = 0
            hovered = -1
            for itm in self.menuItems:
               if itm.rect.collidepoint(e.pos):
                  hovered = i
                  self.selectionMode = mcons.MOUSE # activate mouse mode, if mouse is moved onto a menu item
                  break
               i += 1

            # new item hovered?
            if hovered >= 0 and hovered != self.selectedItem:
               if self.selectedItem >= 0: # reset old hovered item
                  self.menuItems[self.selectedItem].Reset()
               self.selectedItem = hovered
               self.menuItems[self.selectedItem].Hover()
               self.UpdateSelection()
               
            elif self.selectedItem != -1 and hovered == -1 and self.selectionMode == mcons.MOUSE: # only deselect if no item is hovered when in mouse mode
               self.menuItems[self.selectedItem].Reset()
               self.selectedItem = -1
               self.UpdateSelection()
               
         elif e.type == pygame.locals.MOUSEBUTTONUP and e.button == 1 and self.selectionMode==mcons.MOUSE:
            if 0 <= self.selectedItem and self.selectedItem <= len(self.menuItems):
               self.ItemTriggered(self.selectedItem)
               self.selectionMode = mcons.MOUSE
               
   def UpdateSelection(self):
      if not (0 <= self.selectedItem and self.selectedItem < len(self.menuItems)):
         self.selector.visible = False
         return
      
      self.selector.visible = True
      
      itm = self.menuItems[self.selectedItem]
      selector_x = itm.rect.left - (self.selector.rect.width + self.selectorMargin)
      selector_y = itm.rect.centery - math.ceil(0.5*self.selector.rect.height)
      
      self.selector.rect.topleft = selector_x, selector_y
            
class Renderer:
   def __init__(self):
      self.screen = Screen(1024, 768, "testWindow")
      self.clock = pygame.time.Clock()
      
      self.fps = 60
   
   def DrawScene(self, scene):
      scene.Render(self.screen.surface)
      
   def TickFpsClock(self):
      self.clock.tick(self.fps)
            
class Sprite(pygame.sprite.DirtySprite):
   def __init__(self, width, height, z=0, offset=True, flags=0):
      pygame.sprite.DirtySprite.__init__(self)
      
      self.image = MSurface((width, height), flags)
      self.rect = self.image.get_rect()
      self.visible = 1
      self.z = z
      self.offset = offset
      
   def Draw(self, surf, rect=None):
      if self.visible: surf.blit(self.image, self.rect if rect is None else rect)
      
   @staticmethod
   def FromSurface(surf, position=None):
      spr = Sprite(0,0)
      spr.image = surf
      spr.rect = spr.image.get_rect()
      if position: spr.rect.topleft = position
      return spr
   
class SpriteGroup(pygame.sprite.Group):
   """ Subclass of a pygame sprite Group, providing additional functionality.
      Add only 'rpg' Sprites to this group, no pure pygame Sprites, as a Draw() method is required.
       
      - sprites contained in this group may have a z-value, where sprites with
        higher z-values will be drawed on top of lower ones. Sprites with the same
        z-value may be painted in arbitrary order.
        
      - the whole sprite group may be given an offset when drawing, moving all sprite rects by the
        given offset. """
   def __init__(self, *sprites):
      pygame.sprite.Group.__init__(self)
      
      self.zMap = {}       # map containing { 'z': sg } entries where z is a z-coordinate and s1, s2 are all sprites
                           # in this group with that z-coordinate.
      self.zValues = []    # list of all z-coordinates in this group. keep this sorted, as it determines drawing order
      
      self.add(*sprites)
         
   def add(self, *sprites):
      pygame.sprite.Group.add(self, *sprites)
      
      for s in sprites:
         if s.z in self.zValues: self.zMap[s.z].append(s)
         else:
            self.zMap[s.z] = [s]
            self.zValues.append(s.z)
            self.zValues = sorted(self.zValues)
         
   def draw(self, surf, offset=(0,0)):
      for z in self.zValues:
         for spr in self.zMap[z]:
            if spr.offset: spr.Draw(surf, spr.rect.move(offset[0],offset[1]))
            else: spr.Draw(surf)
            
   def remove(self, *sprites):
      pygame.sprite.Group.remove(self, *sprites)
      
      for spr in sprites:
         self.zMap[spr.z].remove(spr)
         if len(self.zMap[spr.z]) == 0:
            del self.zMap[spr.z]
            self.zValues.remove(spr.z)
      
# 
# class Tooltip(Sprite):
#    def __init__(self, text="NO_TEXT"):
#       font = pygame.font.Font(pygame.font.get_default_font(), 14)
#       textColor = (230,230,230,240) 
#       borderColor = (230,230,40,220)
#       background = (0,0,0,180)
#       border = 1
#       
#       textSurf = font.render(text, 1, textColor)
#       
#       Sprite.__init__(self, textSurf.get_rect().width + border + 2, textSurf.get_rect().height + border + 2)
#       self.image.fill(background)
#       pygame.draw.rect(self.image, borderColor, self.image.get_rect().inflate(-2,-2), border)
#       self.image.blitAligned(textSurf, mcons.CENTER)
#       self.image = self.image.convert_alpha()
      
class Tile:
   def __init__(self, x, y, size):
      self.x = x
      self.y = y
      self.size = size
      self.coordinates = (x,y)
      self.rect = pygame.Rect(x*size, y*size, size, size)
      
class MenuItem(Sprite):
   def __init__(self, width, height):
      Sprite.__init__(self, width, height)
      
      self.surfaces = {mcons.DEFAULT: self.image, mcons.HOVERED: self.image, mcons.ACTIVATED: self.image}
      self.state = mcons.DEFAULT
      
   @staticmethod
   def FromSurface(surf):
      spr = MenuItem(0,0)
      spr.image = surf
      spr.surfaces = {mcons.DEFAULT: spr.image, mcons.HOVERED: spr.image, mcons.ACTIVATED: spr.image}
      spr.rect = spr.image.get_rect()
      return spr
   
   def Activate(self):
      self.state = mcons.ACTIVATED
      self.UpdateSurface()
      
   def Hover(self):
      self.state = mcons.HOVERED
      self.UpdateSurface()
      
   def Reset(self):
      self.state = mcons.DEFAULT
      self.UpdateSurface()
   
   def SetActivatedSurface(self, surf):
      self.surfaces[mcons.ACTIVATED] = surf
      
   def SetHoveredSurface(self, surf):
      self.surfaces[mcons.HOVERED] = surf
      
   def UpdateSurface(self):
      self.image = self.surfaces[self.state]
      
class TitleScreen(Scene):
   def __init__(self):
      Scene.__init__(self)
       
      font = pygame.font.Font(pygame.font.match_font("Comic Sans MS"), 180)
       
      logoSpr = Sprite(400, 260)
      pygame.draw.ellipse(logoSpr.image, (180,0,0), logoSpr.rect)
       
      sceneSpr = Sprite(self.screenSize[0], self.screenSize[1])
      sceneSpr.image.blitAligned(logoSpr.image, mcons.CENTER)
      sceneSpr.image.blitAligned(font.render("myrpg", 1, (230,220,0)), mcons.CENTER)
       
      self.sprites.add(sceneSpr)
      
   def ProcessEvents(self):
      events = EventHandler.ProcessEvents(self)
      
      for e in events:
         if e.type == pygame.locals.KEYDOWN and e.key in (pygame.locals.K_RETURN, pygame.locals.K_SPACE)\
           or e.type == pygame.locals.MOUSEBUTTONUP:
            self.nextScene = MainMenu()
            self.flags |= mcons.QUIT
      
class MainMenu(MenuScene):
   def __init__(self):
      MenuScene.__init__(self)
      
      font = pygame.font.Font(pygame.font.match_font("Comic Sans MS"), 40)
      font2 = pygame.font.Font(pygame.font.match_font("Trebuchet"), 32)
      
      sceneSpr = Sprite(self.screenSize[0], self.screenSize[1])
      sceneSpr.image.blitAligned(font.render("Main Menu", 1, (230,220,0)), mcons.TOPLEFT, 20)
      
      self.sprites.add(sceneSpr)
      
      for itm in ("Start game", "Quit"):
         spr = MenuItem.FromSurface(font2.render(itm, 1, (230,230,230)))
         self.AddItem(spr)
         
      self.sprites.add(self.selector)
      
   def ItemTriggered(self, itm):
      if itm == len(self.menuItems)-1: # Quit
         self.nextScene = None
         self.flags |= mcons.QUIT
      elif itm == 0: # Start game
#          stages = [TextEncounterStage("Stage 1", ("Continue...",), stageLinks={0:1}),
#                    TextEncounterStage("Stage 2", ("Quit","Back"), stageLinks={1:0})]
#          enc = TextEncounter(stages)
#          self.nextScene = enc

         self.nextScene = CombatScene("desert.jpg")
         
         #SingleStageTextEncounter("""Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\
         #At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.""")
         self.flags |= mcons.QUIT

class TextEncounterStage:
   """ Text encounters can consist of multiple stages with different text, options and images. Instances of this class contain all data needed to define an encounter stage
     in a TextEncounter scene. """
   def __init__(self, text="NO_TEXT", options=("Continue...",), sprites=[], stageLinks={}):
      self.text = text
      self.options = options
      self.sprites = sprites
      self.stageLinks = stageLinks
      
class TextEncounter(MenuScene):
   def __init__(self, stages=[]):
      MenuScene.__init__(self)
      
      self.stages = stages
      self.curStage = None
      
      self.borderColor = (230,230,230)
      self.borderMargin = 3
      self.borderWidth = 1
      
      self.imageHeightPct = 0.60
      
      self.textFont = pygame.font.Font(pygame.font.match_font("Times"), 20)
      self.textColor = (230,230,230)
      self.optionColor = (230,80,80)
      self.hoveredOptionColor = (230,230,80)
      self.lineSpacing = 2
      
      self.autoSelect = False
      
      self.InitLayout()
      if len(self.stages) != 0:
         self.Evoke()
      
   def Clear(self):
      """ Remove all sprites except background and all menu items"""
      self.sprites = self.sprites[:1]
      self.menuItems = []
      self.selectedItem = -1
      
   def Evoke(self):
      if len(self.stages) == 0:
         raise ValueError("Trying to evoke TextEncounter, but there are no encounter stages set!")
      
      self.curStage = self.stages[0]
      self.InitStage(self.curStage)
      
   def InitLayout(self):
      imgRect = self.background.rect.inflate(-2*self.borderMargin, 0)
      imgRect.top = self.borderMargin
      imgRect.h = math.floor(self.imageHeightPct * self.screenSize[1])
      
      # save imgRect as object property to render images on it later
      self.imgRect = imgRect.inflate(-2*self.borderMargin, -2*self.borderMargin)
      
      textRect = self.background.rect.inflate(-2*self.borderMargin, 0)
      textRect.top = imgRect.bottom + self.borderMargin
      textRect.h = self.screenSize[1] - imgRect.h - 3*self.borderMargin
      
      # draw rect borders
      pygame.draw.rect(self.background.image, self.borderColor, imgRect, self.borderWidth)
      pygame.draw.rect(self.background.image, self.borderColor, textRect, self.borderWidth)
      
      # save textRect as object property to render text on it later
      self.textRect = textRect.inflate(-2*self.borderMargin, -2*self.borderMargin)
      
   def InitStage(self, stage):
      self.Clear()
      self.curStage = stage
      y_off = self.RenderText(stage.text, self.textRect)
      self.RenderOptions(stage.options, self.textRect.move(0, y_off))
      
   def ItemTriggered(self, number):
      if number in self.curStage.stageLinks:
         self.InitStage(self.stages[self.curStage.stageLinks[number]])
      
   def RenderOptions(self, options, rect):
      y_offset = 0
      
      i = 1
      for opt in options:
         optSurf = self.textFont.render(str(i)+". "+opt, 1, self.optionColor)
         optMi= MenuItem.FromSurface(optSurf)
         optMi.rect.topleft = (rect.left, rect.top+y_offset)
         optMi.SetHoveredSurface(self.textFont.render(str(i)+". "+opt, 1, self.hoveredOptionColor))
         y_offset += optSurf.get_rect().h + self.lineSpacing
         i += 1
         
         self.AddItem(optMi, optMi.rect.left, optMi.rect.top)
      
   def RenderText(self, text, rect):
      y_offset = 0
      
      words = text.split(' ')
      
      # wrap lines
      lines = [""]
      for w in words:
         if lines[-1] == "": lines[-1] = w
         else:
            newline = lines[-1] + " " + w
            newlineSize = self.textFont.size(newline)
         
            if newlineSize[0] > rect.w:
               lines.append(w)
            else:
               lines[-1] = newline
      
      for line in lines:
         lineSurf = self.textFont.render(line, 1, self.textColor)
         lineSpr = Sprite.FromSurface(lineSurf)
         lineSpr.rect.topleft = (rect.x,rect.y+y_offset)
         self.sprites.add(lineSpr)
         y_offset += lineSurf.get_rect().h + self.lineSpacing
         
      return y_offset
      
class SingleStageTextEncounter(MenuScene):
   def __init__(self,text="No text", options=("Continue...",)):
      MenuScene.__init__(self)
      
      self.SetOptions(options)
      self.SetText(text)
      
      self.borderColor = (230,230,230)
      self.borderMargin = 3
      self.borderWidth = 1
      
      self.imageHeightPct = 0.60
      
      self.textFont = pygame.font.Font(pygame.font.match_font("Times"), 20)
      self.textColor = (230,230,230)
      self.optionColor = (230,80,80)
      self.hoveredOptionColor = (230,230,80)
      self.lineSpacing = 2
      
      self.autoSelect = False
      
      self.InitLayout()
      
   def InitLayout(self):
      imgRect = self.background.rect.inflate(-2*self.borderMargin, 0)
      imgRect.top = self.borderMargin
      imgRect.h = math.floor(self.imageHeightPct * self.screenSize[1])
      
      textRect = self.background.rect.inflate(-2*self.borderMargin, 0)
      textRect.top = imgRect.bottom + self.borderMargin
      textRect.h = self.screenSize[1] - imgRect.h - 3*self.borderMargin
      
      pygame.draw.rect(self.background.image, self.borderColor, imgRect, self.borderWidth)
      pygame.draw.rect(self.background.image, self.borderColor, textRect, self.borderWidth)
      
      innerTextRect = textRect.inflate(-2*self.borderMargin, -2*self.borderMargin)
      y_offset = self.RenderText(innerTextRect, self.background.image) + 5* self.lineSpacing
      
      optionTextRect = innerTextRect.move(0,y_offset)
      self.RenderOptions(optionTextRect, self.background.image)
      
   def RenderOptions(self, rect, surface):
      y_offset = 0
      
      i = 1
      for opt in self.options:
         optSurf = self.textFont.render(str(i)+". "+opt, 1, self.optionColor)
         optMi= MenuItem.FromSurface(optSurf)
         optMi.rect.topleft = (rect.left, rect.top+y_offset)
         optMi.SetHoveredSurface(self.textFont.render(str(i)+". "+opt, 1, self.hoveredOptionColor))
         y_offset += optSurf.get_rect().h + self.lineSpacing
         i += 1
         
         self.AddItem(optMi, optMi.rect.left, optMi.rect.top)
      
   def RenderText(self, rect, surface):
      y_offset = 0
      
      words = self.text.split(' ')
      
      # wrap lines
      lines = [""]
      for w in words:
         if lines[-1] == "": lines[-1] = w
         else:
            newline = lines[-1] + " " + w
            newlineSize = self.textFont.size(newline)
         
            if newlineSize[0] > rect.w:
               lines.append(w)
            else:
               lines[-1] = newline
      
      for line in lines:
         lineSurf = self.textFont.render(line, 1, self.textColor)
         surface.blit(lineSurf, (rect.x,rect.y+y_offset))
         y_offset += lineSurf.get_rect().h + self.lineSpacing
         
      return y_offset
   
   def SetOptions(self, options):
      self.options = options
      
   def SetText(self, text):
      self.text = text
      
class SceneManager:
   def __init__(self):
      self.currentScene = None
      self.renderer = Renderer()
      
   def Loop(self):
      if self.currentScene is not None:
         
         # process all events in scene
         self.currentScene.GetEvents()
         self.currentScene.ProcessEvents()
         self.currentScene.Frame()
         
         self.renderer.DrawScene(self.currentScene)
         self.renderer.screen.Update()
         self.renderer.TickFpsClock()
         
         # scene still active?
         if self.currentScene.flags & mcons.QUIT:
            if self.currentScene.nextScene:
               self.SetScene(self.currentScene.nextScene)
            else:
               pygame.quit()
               sys.exit()
   
   def SetScene(self, scene):
      if self.currentScene: self.currentScene.flags = 0
      scene.flags |= mcons.ACTIVE
      self.currentScene = scene
   
class Application:
   def __init__(self):
      pygame.init()
      self.sceneManager = SceneManager()
      
   def StartLoop(self):
      while True:
         self.sceneManager.Loop()

def main():
   app = Application()
   app.sceneManager.SetScene(TitleScreen())
   app.StartLoop()        

if __name__=="__main__":
   main()