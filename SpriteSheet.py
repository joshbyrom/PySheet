import pygame

from PubSub import *
from GameEngine import *

class SpriteSheet(PubSub):
    def __init__(self, filepath):
        PubSub.__init__(self)
        
        self.filepath = filepath
        self.surface = pygame.image.load(filepath)

        self.reels = {}

    def add_reel(self, name, reel):
        self.reels[name] = reel
        self.emit('reel added', [name, reel])

    def get_reel(self, name):
        return self.reels[name]

    def get_active_reels(self):
        return [x for x in self.reels if x.active]


class Reel(PubSub):
    def __init__(self, direction = 'horizontal'):
        PubSub.__init__(self)
        self.direction = direction
        
        self.rects = []

    def load(self, offset, size, frames):
        for index in xrange(frames):
            x, y = self._determine_position(offset, size, index)
            self.rects.append((x, y, size[0], size[1]))

        self.emit('loaded')

    def _determine_position(self, offset, size, index):
        x = offset[0]
        y = offset[1]

        if self.direction == 'horizontal':
            x += size[0] * index
        else:
            y += size[1] * index

        return x, y

class AnimationController(PubSub):
    def __init__(self, spritesheet, name):
        PubSub.__init__(self)
        
        self.spritesheet = spritesheet
        self.name = name
        self.reel = spritesheet.get_reel(name)

        self.position = (0, 0)

        self.active = False
        self.current = 0
        self.last = len(self.reel.rects)
        self.frame_duration = 0

        self.time_since_last_frame_change = 0
        
    def start(self, frame_duration):
        self.current = 0
        self.frame_duration = frame_duration
        self.resume()

        self.time_since_last_frame_change = 0
        self.emit('started')

    def stop(self):
        self.active = False
        self.emit('stopped')

    def resume(self):
        self.active = True

    def update(self, elapsed):
        if not self.active: return

        if self.time_since_last_frame_change >= self.frame_duration:
            self.current = (self.current + 1) % self.last
            if self.current < 0:
                self.current += self.last
            self.time_since_last_frame_change = 0

            if self.current == (self.last - 1):
                print finished

        self.time_since_last_frame_change += elapsed

    def get_current_surface(self):
        rect = self.reel.rects[self.current]
        surface = self.spritesheet.surface.subsurface(rect)
        return surface
            


class SpriteSheetView(PubSub):
    def __init__(self, spritesheet):
        PubSub.__init__(self)

        self.spritesheet = spritesheet
        self.spritesheet.on('reel added', self.handle_reel)
        self.position = (0, 0)

        self.animation_controllers = []
        self.update_hooked = False

    def handle_reel(self, spritesheet, event, args):
        name, reel = args
        controller = AnimationController(self.spritesheet, name)
        self.animation_controllers.append(controller)
        
    def render(self, engine, event, surface):
        self.hook_animation_loop(engine)

        for controller in self.animation_controllers:
            if controller.active:
                position = [self.position[x] + controller.position[x]
                            for x in xrange(len(self.position))]

                c_surface = controller.get_current_surface()
                surface.blit(c_surface, (position[0],
                                         position[1],
                                         c_surface.get_width(),
                                         c_surface.get_height()))
            

    def hook_animation_loop(self, engine):
        if not self.update_hooked:
            engine.on('tick', self.update)
            self.update_hooked = True
            

    def update(self, engine, event, elapsed):
        for controller in self.animation_controllers:
            controller.update(elapsed)


    def start_animation(self, name, duration):
        return len([x.start(duration)
                    for x in self.animation_controllers
                        if x.name == name])

    def stop_animation(self, name):
        return len([x.stop()
                    for x in self.animation_controllers
                        if x.name == name])
            
if __name__ == '__main__':
    import os
    import sys

    filepath = os.path.join(sys.path[0], 'mon3_sprite_base.png')

    def on_init(engine, event, *args):
        sheet = SpriteSheet(filepath)
        view = SpriteSheetView(sheet)
        
        idle = Reel()
        idle.load((0, 0), (64, 64), 5)
        sheet.add_reel('idle', idle)

        atk = Reel()
        atk.load((0, 64), (64, 64), 5)
        sheet.add_reel('attack', atk)

        hurt = Reel()
        hurt.load((0, 128), (64, 64), 3)
        sheet.add_reel('hurt', hurt)

        dead = Reel()
        dead.load((0, 128), (64, 64), 7)
        sheet.add_reel('dead', dead)

        view.start_animation('idle', 200)
        engine.on('render', view.render)

        
    engine = Engine()
    engine.on('init', on_init)
    engine.set_caption('SpriteSheet Unit Test')
    engine.start()
