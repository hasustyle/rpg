# -*- coding: utf-8 -*-
import pygame, pygame.locals, sys, mcons, math, os
import ruleset as rs

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
   def __init__(self):
      EventHandler.__init__(self)
      self.sprites = []
      self.flags = 0
      self.nextScene = None
      self.screenSize = (800,  600)
      
   def Frame(self):
      pass
      
   def Render(self, surface):
      for sprite in self.sprites:
         sprite.Draw(surface)
#      self.eventHandler = EventHandler()
#       
#       self.sprites.append(Sprite(self.screenSize[0],self.screenSize[1]))
#       
#    def SetBackground(self, color):
#       self.sprites[0].image.fill(color)

class Creature:
   def __init__(self, sprite=None):
      self.sprites = {mcons.DEFAULT:sprite}
      self.state = mcons.DEFAULT
      
      self.pos = [0., 0.] if sprite is None else [1.*sprite.rect.centerx, 1.*sprite.rect.centery]
      
      self.profile = rs.RPGCreature("Alrik", 1, rs.RPGRace("Human"), rs.RPGProfession("Warrior"))
      
   def GetSprite(self):
      return self.sprites[self.state] if self.state in self.sprites else self.sprites[mcons.DEFAULT]
   
   def GetTooltip(self):
      return Tooltip(str(self.profile))

class CombatScene(Scene):
   ScrollKeys = (pygame.locals.K_UP, pygame.locals.K_DOWN, pygame.locals.K_LEFT, pygame.locals.K_RIGHT)
   
   def __init__(self, backgroundImg=""):
      Scene.__init__(self)
      
      self.mapSizeX, self.mapSizeY = (21.,21.) # map size in meters/physical length unit
      self.ppm = 64. # zoom factor / pixels per meter
      self.tileSize = 1.5 # tile size in meters/physical length
      self.scrollSpeed = 0.13
      self.movementSpeed = 6.
      
      self.cameraX, self.cameraY = (0.,0.) # top left corner of camera
      
      self.gridColor = (20,180,250,210)
      self.gridBgA = (10,90,125,150)
      self.gridBgB = (8,72,100,150)
      
      self.scrolling = False
      self.movingCreature = False
      self.showGrid = False
      self.showActiveTile = False
      
      self.scrollRects = {
            mcons.SCROLL_UP:    pygame.Rect(0,0,800,640/10),
            mcons.SCROLL_DOWN:  pygame.Rect(0,640-640/10,800,640/10),
            mcons.SCROLL_LEFT:  pygame.Rect(0,0,800/10,640),
            mcons.SCROLL_RIGHT: pygame.Rect(800-800/10,0,800/10,640)}
      
      if mcons.DEBUG:
         self.mapArea = Sprite(self.mapSizeX*self.ppm, self.mapSizeY*self.ppm)
         self.mapArea.image.fill((40,150,150))
         self.sprites.append(self.mapArea)
      
      self.background = Sprite(self.mapSizeX*self.ppm, self.mapSizeY*self.ppm)
      if backgroundImg != "":
         self.background.image.blit(pygame.image.load(os.path.join("gfx",backgroundImg)).convert(), (0,0))
      self.sprites.append(self.background)
      
      
      size = self.tileSize * self.ppm
      self.grid = Sprite(self.mapSizeX*self.ppm, self.mapSizeY*self.ppm)
      self.grid.visible = False
      self.grid.image = self.grid.image.convert_alpha()
      for i in range(int(self.mapSizeX//self.tileSize)):
         for j in range(int(self.mapSizeY//self.tileSize)):
            color = self.gridBgA if (i+j%2)%2 == 0 else self.gridBgB
            pygame.draw.rect(self.grid.image, color, (i*size, j*size, size, size)) # tile background
            pygame.draw.rect(self.grid.image, self.gridColor, (i*size, j*size, size, size), 1) # tile border
      self.sprites.append(self.grid)
      
      self.hoveredTileSprite = Sprite(size, size)
      self.hoveredTileSprite.visible = False
      self.hoveredTileSprite.image = self.hoveredTileSprite.image.convert_alpha()
      pygame.draw.rect(self.hoveredTileSprite.image, (0,0,0,0), (0,0,size,size))
      pygame.draw.rect(self.hoveredTileSprite.image, (255,255,255), (0,0,size,size), 1)
      self.sprites.append(self.hoveredTileSprite)
      
      self.AddCreature(Creature(Sprite.FromSurface(pygame.image.load(os.path.join("gfx","hero.png")).convert())))
      
      self.InitTiles()
      
   def AddCreature(self, creature):
      self.sprites.append(creature.GetSprite())
      self.creature=creature
      
   def Frame(self):
      dx, dy = 0., 0.
      if self.scrollRects[mcons.SCROLL_UP].collidepoint(pygame.mouse.get_pos()): dy -= 1.
      if self.scrollRects[mcons.SCROLL_DOWN].collidepoint(pygame.mouse.get_pos()): dy += 1.
      if self.scrollRects[mcons.SCROLL_LEFT].collidepoint(pygame.mouse.get_pos()): dx -= 1.
      if self.scrollRects[mcons.SCROLL_RIGHT].collidepoint(pygame.mouse.get_pos()): dx += 1.
      self.MoveCamera(self.scrollSpeed*dx, self.scrollSpeed*dy)
      
      if self.scrolling:
         dx, dy = 0., 0.
         if pygame.locals.K_UP in self.pressedKeys: dy -= 1.
         if pygame.locals.K_DOWN in self.pressedKeys: dy += 1.
         if pygame.locals.K_LEFT in self.pressedKeys: dx -= 1.
         if pygame.locals.K_RIGHT in self.pressedKeys: dx += 1.
         self.MoveCamera(self.scrollSpeed*dx, self.scrollSpeed*dy)
      
      if self.movingCreature:
         target = pygame.mouse.get_pos()[0]+self.cameraX*self.ppm, pygame.mouse.get_pos()[1]+self.cameraY*self.ppm
         curpos = self.creature.pos
         
         dx = 1. * target[0] - curpos[0]
         dy = 1. * target[1] - curpos[1]
         dist2 = dx**2+dy**2
         if dist2 <= 1.: return
         angle = math.atan2(dy, dx)
         move_r = min( self.movementSpeed, math.sqrt(dist2) )
         
         self.MoveCreature(move_r*math.cos(angle),move_r*math.sin(angle))
         
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
      
   def MoveCreature(self, dx, dy):
      self.creature.pos[0] += dx
      self.creature.pos[1] += dy
      
      self.creature.GetSprite().rect.center = (self.creature.pos[0],self.creature.pos[1]) 
      
   def ProcessEvents(self):
      events = EventHandler.ProcessEvents(self)
      mousepos = pygame.mouse.get_pos()[0]+self.cameraX*self.ppm, pygame.mouse.get_pos()[1]+self.cameraY*self.ppm
      
      for e in events:
         if e.type == pygame.locals.KEYDOWN:
            if e.key in CombatScene.ScrollKeys:
               self.scrolling = True
            
            elif e.key == pygame.locals.K_g:
               self.showGrid = not self.showGrid 
            
            elif e.key == pygame.locals.K_h:
               self.showActiveTile = not self.showActiveTile
               
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
            
            if self.HoveredTile():
               self.hoveredTileSprite.rect = self.HoveredTile().rect
               
#             if self.creature.GetSprite().rect.collidepoint(mousepos):
#                self.sprites.append(self.creature.GetTooltip())
               
         elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
               self.movingCreature=True
#             elif e.button == 4:
#                self.Zoom(1)
#             elif e.button == 5:
#                self.Zoom(-1)
               
         elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1:
               self.movingCreature=False
      
   def Render(self, surface):
      surface.fill((0,0,0)) # draw black background because screen might be larger than combat area
      for sprite in self.sprites:
         #if sprite.visible: surface.blit(sprite.image, sprite.rect.move(-self.cameraX*self.ppm, -self.cameraY*self.ppm))
         sprite.Draw(surface, sprite.rect.move(-self.cameraX*self.ppm, -self.cameraY*self.ppm))
         
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
      self.sprites.append(self.background)

   def AddItem(self, item, x=-1, y=-1):
      """ Adds a sprite as a menu item and tries to position it automatically, by placing it beneath the
         last item. Positionig can be manually overwritten."""
      if y<0 and len(self.menuItems) > 0:
         iy = self.menuItems[-1].rect.bottom + self.itemSpacing
      elif y<0:
         iy = 3*self.itemSpacing
      else: #manual placement
         iy = y
      
      if x<0 and len(self.menuItems) > 0:
         if self.itemAlignment & mcons.LEFT:
            ix = self.menuItems[-1].rect.left
         elif self.itemAlignment & mcons.RIGHT:
            ix = self.menuItems[-1].rect.right - item.rect.width
         elif self.itemAlignment & mcons.HCENTER:
            ix = self.menuItems[-1].rect.centerx - math.floor(0.5*item.rect.width)
      elif x<0:
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
      self.sprites.append(item)
      
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
      self.screen = Screen(800, 600, "testWindow")
      self.clock = pygame.time.Clock()
      
      self.fps = 60
   
   def DrawScene(self, scene):
      scene.Render(self.screen.surface)
      
   def TickFpsClock(self):
      self.clock.tick(self.fps)
            
class Sprite(pygame.sprite.Sprite):
   def __init__(self, width, height):
      pygame.sprite.Sprite.__init__(self)
      
      self.image = MSurface((width, height))
      self.rect = self.image.get_rect()
      self.visible = True
      
   def Draw(self, surf, rect=None):
      if self.visible: surf.blit(self.image, self.rect if rect is None else rect)
      
   @staticmethod
   def FromSurface(surf):
      spr = Sprite(0,0)
      spr.image = surf
      spr.rect = spr.image.get_rect()
      return spr

class Tooltip(Sprite):
   def __init__(self, text="NO_TEXT"):
      font = pygame.font.Font(pygame.font.get_default_font(), 14)
      textColor = (230,230,230,240) 
      borderColor = (230,230,40,220)
      background = (0,0,0,180)
      border = 1
      
      textSurf = font.render(text, 1, textColor)
      
      Sprite.__init__(self, textSurf.get_rect().width + border + 2, textSurf.get_rect().height + border + 2)
      self.image.fill(background)
      pygame.draw.rect(self.image, borderColor, self.image.get_rect().inflate(-2,-2), border)
      self.image.blitAligned(textSurf, mcons.CENTER)
      self.image = self.image.convert_alpha()
      
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
       
      self.sprites.append(sceneSpr)
      
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
      
      self.sprites.append(sceneSpr)
      
      for itm in ("Start game", "Quit"):
         spr = MenuItem.FromSurface(font2.render(itm, 1, (230,230,230)))
         self.AddItem(spr)
         
      self.sprites.append(self.selector)
      
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
         self.sprites.append(lineSpr)
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