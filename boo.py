#Contains the class that represents Boo, Thornton's cohort.

import pygame, math, random
from snake_player import *
from collections import namedtuple
from colors import *
from block import *
from los import *
from weapons import *

B_SNAKE_COLLIDE_DAM = 3

#11 is a reasonable chase speed

class Boo(pygame.sprite.Sprite):
    '''A class that represents Boo.'''
    
    def __init__(self: "Enemy", window: "Canvas", trigger_happiness: [int] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
                 keeps_dist: bool = False, chase_speed: int = 11, patrol_speed: int = 4, attack_box: (int) = (10, 10, 10, 10),
                 hover_dist: float = 0):
        '''Initializes the attributes of a Snake Sprite.'''
        pygame.sprite.Sprite.__init__(self)
        #self.image = pygame.Surface((width, height)) #Must set the image attribute so that the sprite appears
        self.image = pygame.image.load("boo_south0.png")
        #self.image.fill(color) #If you have an actual picture, don't fill!!!
        self.rect = self.image.get_rect() #Must set the rect attribute so that you can
                                          #"grab" the Sprite by coordinates on the rect
        
        self.patrol_route = [] #Will be set by an Area object
        self._instr_index = 0
        self._current_step_num = self._current_wait_num = \
                                 self._current_look_num = 0
        self._is_moving = False
        self._looking_north = self._looking_east = \
                            self._looking_south = self._looking_west = False

        self._cur_frame = 0
        self._north_imgs = ["boo_north0.png", "boo_north1.png", "boo_north2.png"]
        self._east_imgs = ["boo_east0.png", "boo_east1.png", "boo_east2.png"]
        self._south_imgs = ["boo_south0.png", "boo_south1.png", "boo_south2.png"]
        self._west_imgs = ["boo_west0.png", "boo_west1.png", "boo_west2.png", "boo_west3.png"]
        self._stunned_imgs = ["enemy_stunned1.png", "enemy_stunned2.png"]
        
        self._view_obstructed = False
        #self.in_alert_phase = True #Set this to True for testing

        self.area = None

        ## LINE OF SIGHT STUFF ##
        self.window = window

        ## ATTACKING STUFF ## I think I'll just let basically all of these be arguments. 6 args probably.
        self.trigger_happiness = trigger_happiness
        
        #This attribute is here to avoid all Enemies from having the same AI (cuz then they'd eventually flock)
        self.keeps_dist = keeps_dist #(default will ultimately be false)...Might be renamed to keeps_distance...so distance value could be adjust too
        self.chase_speed = chase_speed #7 pixels per iteration
        
        self.v_chase_move = 0 #FOR COLLISION STUFF
        self.h_chase_move = 0 #FOR COLLISON STUFF
        
        self.patrol_speed = patrol_speed

        self.ab_left_x, self.ab_right_x, self.ab_top_y, self.ab_bottom_y = attack_box[0], attack_box[1], attack_box[2], attack_box[3]

        self.hover_dist = hover_dist #Used in conjunction with keeps_dist. was 320 before...think of this as a radius for an Enemy

        self._collide_while_north = self._collide_while_east = self._collide_while_south = self._collide_while_west = False
        self._is_colliding = False

        self._nav_from_north_right = self._nav_from_north_left = False
        self._nav_from_south_right = self._nav_from_south_left = False
        self._nav_from_west_bottom = self._nav_from_west_top = False
        self._nav_from_east_bottom = self._nav_from_east_top = False
        

        #FOR BOSS BATTLES
        self.is_boss = True
        self.is_frost = False
        self.is_boo = True
        self.health = 100

        self.is_stunned = False
        self.stun_time = 0

        self.stun_location = None
        

    def init_position(self: "Enemy", x: float, y: float):
        '''Initializes the position of Snake on the game display.'''
        self.rect.centerx = x
        self.rect.centery = y


    #In order to actually have the Sprite do anything, you need to call its update() method
    def update(self: "Enemy", collidables: "Group", snake_group: "Group", s_attack_obj_group: "Group"): #update could be where I increment the steps taken by the Enemy
        '''Sets all the necessary updates to the state of an Enemy Sprite.'''
        obj_collisions_lst = pygame.sprite.spritecollide(self, collidables, False)
        #^...Collisions between objects and Enemies...
        snake_collision_lst = pygame.sprite.spritecollide(self, snake_group, False)
        #^...Collisions between Snake and the Enemy...
        s_attack_obj_collision_lst = pygame.sprite.spritecollide(self, s_attack_obj_group, False)
        snake = list(snake_group)[0]
        dist_from_snake = math.sqrt((snake.rect.centerx - self.rect.centerx)**2 + (snake.rect.centery - self.rect.centery)**2)
        #^Euclidean distance. Think of this as something that creates a circle around an Enemy. THIS DISTANCE VALUE MUST NOT BE WITHIN THE ATTACK SQUARE
        
        if obj_collisions_lst == []:
            self._pursue_snake(snake, dist_from_snake)
        elif obj_collisions_lst != []:
            self._handle_physical_object_collisions(obj_collisions_lst, snake)
            
        self._handle_collision_with_snake(snake_collision_lst)                
        self._determine_animation()


    def _pursue_snake(self: "Enemy", snake: "Snake", dist_from_snake: float):
        '''Conducts the necessary checks for Snake's location to allow this Enemy to pursue him.'''
        self._is_moving = True
        if snake.rect.centery > self.rect.centery+self.ab_bottom_y:  #Snake is south of an Enemy's attack box
            if self.keeps_dist:
                #if Snake is south and to the left/right of centerx and far away, then move left/right instead of down right away
                self._keep_dist_for_north_or_south_snake("south", snake, dist_from_snake)
            else: #These lines are what was originally in: if snake.rect.centery > self.rect.centery+self.ab_bottom_y
                self._go_chase_south()
        elif snake.rect.centery < self.rect.centery-self.ab_top_y: #Snake is north of an Enemy's attack box
            if self.keeps_dist:
                #if Snake is north and to the left/right of centerx and far away, then move left/right instead of up right away
                self._keep_dist_for_north_or_south_snake("north", snake, dist_from_snake)
            else:
                self._go_chase_north()
        elif snake.rect.centerx > self.rect.centerx+self.ab_right_x: #Snake is east of an Enemy's attack box
            if self.keeps_dist:
                #if Snake is east and to the top/bottom of centery and far away, then move up/down instead of right right away
                self._keep_dist_for_east_or_west_snake("east", snake, dist_from_snake)
            else:
                self._go_chase_east()
        elif snake.rect.centerx < self.rect.centerx-self.ab_left_x: #Snake is west of an Enemy's attack box
            if self.keeps_dist:
                #if Snake is west and to the top/bottom of centery and far away, then move up/down instead of left right away
                self._keep_dist_for_east_or_west_snake("west", snake, dist_from_snake)
            else:
                self._go_chase_west()
        else: #Else, Snake is within the attack box
            self._is_moving = False
            self._turn_while_in_attack_box(snake)


    def _handle_physical_object_collisions(self: "Enemy", obj_collisions_lst: ["Sprites"], snake: "Snake"):
        '''Handles collisions between this Enemy and a physical object that is an obstacle in its path.'''
        obj = obj_collisions_lst[0]
        moving_south_obj_collide = (obj.rect.bottom > self.rect.bottom > obj.rect.top and obj.rect.bottom > self.rect.top < obj.rect.top and
            (obj.rect.right > self.rect.right > obj.rect.left and obj.rect.right > self.rect.left > obj.rect.left))
        moving_north_obj_collide = (obj.rect.top < self.rect.top < obj.rect.bottom and obj.rect.bottom < self.rect.bottom > obj.rect.top and
              (obj.rect.right > self.rect.right > obj.rect.left and obj.rect.right > self.rect.left > obj.rect.left))
        moving_west_obj_collide = (obj.rect.right > self.rect.left > obj.rect.left and obj.rect.left < self.rect.right > obj.rect.right and
              (obj.rect.top < self.rect.bottom < obj.rect.bottom and obj.rect.top < self.rect.top < obj.rect.bottom))
        moving_east_obj_collide = (obj.rect.left < self.rect.right < obj.rect.right and obj.rect.left > self.rect.left < obj.rect.right and
              (obj.rect.top < self.rect.bottom < obj.rect.bottom and obj.rect.top < self.rect.top < obj.rect.bottom))
        top_right_edge_case = (obj.rect.bottom > self.rect.bottom >= obj.rect.top and obj.rect.bottom > self.rect.top <= obj.rect.top and
             self.rect.right >= obj.rect.right)
        top_left_edge_case = (obj.rect.bottom > self.rect.bottom >= obj.rect.top and obj.rect.bottom > self.rect.top <= obj.rect.top and  
             self.rect.left <= obj.rect.left)
        bottom_left_edge_case = (obj.rect.bottom >= self.rect.top > obj.rect.top and obj.rect.top < self.rect.bottom >= obj.rect.bottom and  
              self.rect.left <= obj.rect.left)
        bottom_right_edge_case = (obj.rect.bottom >= self.rect.top > obj.rect.top and obj.rect.top < self.rect.bottom >= obj.rect.bottom and  
              self.rect.right >= obj.rect.right)

        self._navigate_around_objects(moving_south_obj_collide, moving_north_obj_collide, moving_east_obj_collide,
                                      moving_west_obj_collide, top_right_edge_case, top_left_edge_case, bottom_left_edge_case,
                                      bottom_right_edge_case, snake) 



    def _navigate_around_objects(self: "Enemy", moving_south_obj_collide: bool, moving_north_obj_collide: bool,
                                 moving_east_obj_collide: bool, moving_west_obj_collide: bool, top_right_edge_case: bool,
                                 top_left_edge_case: bool, bottom_left_edge_case: bool, bottom_right_edge_case: bool, snake: "Snake"):
        '''Performs a series of checks that determine how this Enemy will navigate around an object
           that it has collided with.'''
        if (moving_south_obj_collide):
            self._navigate_obj_going_south(snake)
        elif (moving_north_obj_collide):
            self._navigate_obj_going_north(snake)
        elif (moving_west_obj_collide):
            self._navigate_obj_going_west(snake)
        elif (moving_east_obj_collide):
            self._navigate_obj_going_east(snake)
        elif (top_right_edge_case):
            self._navigate_top_right_edge()
        elif (top_left_edge_case):
            self._navigate_top_left_edge()
        elif (bottom_left_edge_case):
            self._navigate_bottom_left_edge()
        elif (bottom_right_edge_case):
            self._navigate_bottom_right_edge()
        else:
            self._navigate_smaller_objs(snake)    



    def _navigate_top_right_edge(self):
        '''Updates the necessary attributes to allow this Enemy to navigate around the top right edge
           of some physical object.'''
        #print("TOP RIGHT EDGE")
        if self.h_chase_move < 0:
            self.rect.centery -= 10
        elif self.v_chase_move > 0:
            self.rect.centerx += 10
        elif self._nav_from_south_right:
            self._go_chase_east()
        elif self._nav_from_west_top:
            self._go_chase_north()


    def _navigate_top_left_edge(self):
        '''Updates the necessary attributes to allow this Enemy to navigate around the top left edge
           of some physical object.'''
        #print("TOP LEFT EDGE")
        if self.h_chase_move > 0:
            self.rect.centery -= 10
        elif self.v_chase_move > 0:
            self.rect.centerx -= 10
        elif self._nav_from_south_left:
            self._go_chase_west()
        elif self._nav_from_east_top:
            self._go_chase_north()


    def _navigate_bottom_left_edge(self):
        '''Updates the necessary attributes to allow this Enemy to navigate around the bottom left edge
           of some physical object.'''
        #print("BOTTOM LEFT EDGE")
        if self.h_chase_move > 0:
            self.rect.centery += 10
        elif self.v_chase_move < 0:
            self.rect.centerx -= 10
        elif self._nav_from_north_left:
            self._go_chase_west()
        elif self._nav_from_east_bottom:
            self._go_chase_south()


    def _navigate_bottom_right_edge(self):
        '''Updates the necessary attributes to allow this Enemy to navigate around the bottom right edge
           of some physical object.'''
        #print("BOTTOM RIGHT EDGE")
        if self.h_chase_move < 0:
            self.rect.centery += 10
        elif self.v_chase_move < 0:
            self.rect.centerx += 10
        elif self._nav_from_north_right:
            self._go_chase_east()
        elif self._nav_from_west_bottom:
            self._go_chase_south()


    def _navigate_obj_going_south(self: "Enemy", snake):
        '''Updates the necessary attributes to allow this Enemy to navigate around a physical object
           while moving south.'''
        if snake.rect.centery > self.rect.centery: #If Snake is below the Enemy...
            #Watch out. Enemy will oscillate between these two if statements if Snake is on same vertical line as Enemy
            if snake.rect.centerx > self.rect.centerx:
                self._nav_from_south_right = True
                self._nav_from_south_left = False
                self._go_chase_east()
            elif snake.rect.centerx < self.rect.centerx:
                self._nav_from_south_left = True
                self_nav_from_south_right = False
                self._go_chase_west()
        elif snake.rect.centery <= self.rect.centery: #If Snake is above the Enemy...
            self._nav_from_south_left = self._nav_from_south_right = False
            self._go_chase_north()
            #Without this elif, this Enemy would keep on tracing the border of a physical object until it is no longer touching it.
            #This elif effectively aborts the tracing.


    def _navigate_obj_going_north(self: "Enemy", snake: "Snake"):
        '''Updates the necessary attributes to allow this Enemy to navigate around a physical object
           while moving north.'''
        if snake.rect.centery < self.rect.centery:
            if snake.rect.centerx > self.rect.centerx:
                self._nav_from_north_right = True
                self._nav_from_north_left = False
                self._go_chase_east()
            elif snake.rect.centerx < self.rect.centerx:
                self._nav_from_north_left = True
                self_nav_from_north_right = False
                self._go_chase_west()
        elif snake.rect.centery >= self.rect.centery:
            self._nav_from_north_left = self._nav_from_north_right = False
            self._go_chase_north()


    def _navigate_obj_going_west(self: "Enemy", snake: "Snake"):
        '''Updates the necessary attributes to allow this Enemy to navigate around a physical object
           while moving west.'''
        #print("snake's centery: ", snake.rect.centery)
        #print("self.rect.bottom: ", self.rect.bottom)
        #print("self.rect.top: ", self.rect.top)
        if snake.rect.centerx < self.rect.centerx:
            if snake.rect.centery > self.rect.centery:
                #print("HERE1")
                self._nav_from_west_bottom = True
                self._nav_from_west_top = False
                self._go_chase_south()
            elif snake.rect.centery < self.rect.centery:
                #print("HERE2")
                self._nav_from_west_top = True
                self._nav_from_west_bottom = False
                self._go_chase_north()
        elif snake.rect.centerx >= self.rect.centerx:
            self._nav_from_west_top = self._nav_from_west_bottom = False
            self._go_chase_west()


    def _navigate_obj_going_east(self: "Enemy", snake: "Snake"):
        '''Updates the necessary attributes to allow this Enemy to navigate around a physical object
           while moving east.'''
        if snake.rect.centerx > self.rect.centerx: #If Snake is right of the Enemy...
            if snake.rect.centery > self.rect.centery: #Snake is bottom
                self._nav_from_east_top = False
                self._nav_from_east_bottom = True
                self._go_chase_south()
            elif snake.rect.centery < self.rect.centery: #Snake is Top
                self._nav_from_east_bottom = False
                self._nav_from_east_top = True
                self._go_chase_north()
        elif snake.rect.centerx <= self.rect.centerx: #If Snake is right of the Enemy...
            self._nav_from_east_top = self._nav_from_east_bottom = False
            self._go_chase_east()


    def _navigate_smaller_objs(self: "Enemy", snake: "Snake"): #Think about the problem you had with the smaller blue square
        '''Updates the necessary attributes for allowing enemies to navigate around objects smaller than them.'''
        if self._looking_east or self._looking_west:
            if snake.rect.y > self.rect.centery:
                self.rect.y += 10
            elif snake.rect.y <= self.rect.centery:
                self.rect.y -= 10
        elif self._looking_north or self._looking_south:
            if snake.rect.x > self.rect.centerx:
                self.rect.x += 10
            elif snake.rect.x <= self.rect.centerx:
                self.rect.x -= 10


    def _turn_while_in_attack_box(self, snake):
        '''Sets any attributes necessary for allowing an Enemy to turn towards Snake while Snake is in its attack box.'''        
        if ((snake.rect.centery < self.rect.centery or snake.rect.centery >= self.rect.centery)
            and (snake.rect.centerx > self.rect.centerx+0.75*self.ab_right_x)):
            #print("SHOOTING EAST")
            self._set_orientation("east")
            self.image = pygame.image.load("boo_east0.png")
        elif (snake.rect.centery >= self.rect.centery and
              (self.rect.centerx-0.75*self.ab_left_x <= snake.rect.centerx <= self.rect.centerx+0.75*self.ab_right_x)):
            #print("SHOOTING SOUTH")
            self._set_orientation("south")
            self.image = pygame.image.load("boo_south0.png")
        elif ((snake.rect.centery < self.rect.centery or snake.rect.centery >= self.rect.centery)
              and (snake.rect.centerx < self.rect.centerx-0.75*self.ab_left_x)):
            #print("SHOOTING WEST")
            self._set_orientation("west")
            self.image = pygame.image.load("boo_west0.png")
        elif (snake.rect.centery <= self.rect.centery and
              (self.rect.centerx-0.75*self.ab_left_x <= snake.rect.centerx <= self.rect.centerx+0.75*self.ab_right_x)):
            self._set_orientation("north")
            self.image = pygame.image.load("boo_north0.png")



    def _set_collision_dir(self, direction):
        '''Sets the collision_while_[direction] attribute according to what direction this Enemy
           was moving in when collision occurred.'''
        if direction == "north":
            self._collide_while_south = self._collide_while_east = self._collide_while_west = False
            self._collide_while_north = True
        elif direction == "east":
            self._collide_While_north = self._collide_while_south = self._collide_while_west = False
            self._collide_while_east = True
        elif direction == "south":
            self._collide_while_north = self._collide_while_east = self._collide_while_west = False
            self._collide_while_south = True          
        elif direction == "west":
            self._collide_while_north = self._collide_while_east = self._collide_while_south = False
            self._collide_while_west = True


    def _keep_dist_for_north_or_south_snake(self, direction, snake, dist_from_snake): #STILL NEEDED TO PASS dist_from_snake to here
        '''Causes Boo to keep its distance from Snake while Boo is going north or south.'''
        #print("KEEP DIST NORTH OR SOUTH")
        if snake.rect.centerx < self.rect.centerx and dist_from_snake > self.hover_dist: #Snake is left
            self._go_chase_west()
        elif snake.rect.centerx >= self.rect.centerx and dist_from_snake > self.hover_dist: #Snake is right
            self._go_chase_east()
        else: #Code here should be similar to code in the if/else statement this function is called from
            if direction == "south":
                self._go_chase_south()
            else:
                self._go_chase_north()


    def _keep_dist_for_east_or_west_snake(self, direction, snake, dist_from_snake): #STILL NEEDED TO PASS dist_from_snake to here
        '''Causes Boo to keep its distance from Snake while Boo is going east or west.'''
        #print("KEEP DIST EAST OR WEST")
        if snake.rect.centery < self.rect.centery and dist_from_snake > self.hover_dist: #Snake is top
            self._go_chase_north()
        elif snake.rect.centery >= self.rect.centery and dist_from_snake > self.hover_dist: #Snake is bottom
            self._go_chase_south()
        else:
            if direction == "east":
                self._go_chase_east()
            else:
                self._go_chase_west()

                            
    def _go_chase_north(self):
        '''Chase in the northern direction.'''
        self._set_orientation("north")
        self.h_chase_move = 0 #To ensure no diagonal movements
        self.v_chase_move = -self.chase_speed
        self.rect.y += self.v_chase_move
        #self.rect.y -= self.chase_speed #move up
    
    def _go_chase_east(self):
        '''Chase in the eastern direction.'''
        self._set_orientation("east")
        self.v_chase_move = 0
        self.h_chase_move = self.chase_speed
        self.rect.x += self.h_chase_move #move right
        #self.rect.x += self.chase_speed #move right

    def _go_chase_south(self):
        '''Chase in the southern direction.'''
        self._set_orientation("south")
        self.h_chase_move = 0
        self.v_chase_move = self.chase_speed
        self.rect.y += self.v_chase_move
        #self.rect.y += self.chase_speed #move down

    def _go_chase_west(self):
        '''Chase in the western direction.'''
        self._set_orientation("west")
        self.v_chase_move = 0
        self.h_chase_move = -self.chase_speed
        self.rect.x += self.h_chase_move #move left
        #self.rect.x -= self.chase_speed #move left    

            
    def _set_orientation(self, direction):
        '''Sets the directional orientation of an Enemy'''
        if direction == "north":
            self._looking_south = self._looking_east = self._looking_west = False
            self._looking_north = True
        elif direction == "east":
            self._looking_north = self._looking_south = self._looking_west = False
            self._looking_east = True
        elif direction == "south":
            self._looking_north = self._looking_east = self._looking_west = False
            self._looking_south = True          
        elif direction == "west":
            self._looking_north = self._looking_east = self._looking_south = False
            self._looking_west = True


    def _determine_movement(self, movement, units):
        '''Determines the movement to be processed for an Enemy on patrol.'''
        if movement == "go_east":
            self._set_go_east_movement(units)
        elif movement == "go_west":
            self._set_go_west_movement(units)
        elif movement == "go_north":
            self._set_go_north_movement(units)
        elif movement == "go_south":
            self._set_go_south_movement(units)
        elif movement == "wait":
            self._set_wait_movement(units)
        elif movement == "look_east":
            self._set_look_east_movement(units)
        elif movement == "look_west":
            self._set_look_west_movement(units)
        elif movement == "look_north":
            self._set_look_north_movement(units)
        elif movement == "look_south":
            self._set_look_south_movement(units)
        elif movement == "end":
            self._instr_index = 0
                

    def _determine_animation(self):
        '''Determines the appropriate animation for this Enemy based on the direction in which
           it is facing.'''
        if self._is_moving:
            if self._looking_south:
                self._animate(self._south_imgs)
            elif self._looking_north:
                self._animate(self._north_imgs)
            elif self._looking_east:
                self._animate(self._east_imgs)
            elif self._looking_west:
                self._animate(self._west_imgs)


    def _handle_collision_with_snake(self, snake_collision_lst):
        '''Handles a collision with Snake.'''
        if len(snake_collision_lst) > 0:
            boo_growl = pygame.mixer.Sound("boo_growl.wav")
            pygame.mixer.Sound.play(boo_growl)
            self.area.player_obj.health -= B_SNAKE_COLLIDE_DAM
        

    def _set_look_north_movement(self: "Enemy", units :int):
        '''Takes units of movement and sets the necessary attributes
           for a look north movement.'''
        if self._current_look_num <= units:
            self.image = pygame.image.load("boo_north0.png")
            self._looking_north = True
            self._current_look_num += 1
        else:
            self._instr_index += 1
            self._looking_north = False
            self._current_look_num = 0


    def _set_look_south_movement(self: "Enemy", units :int):
        '''Takes units of movement and sets the necessary attributes
           for a look south movement.'''
        if self._current_look_num <= units:
            self.image = pygame.image.load("boo_south0.png")
            self._looking_south = True
            self._current_look_num += 1
        else:
            self._instr_index += 1
            self._looking_south = False
            self._current_look_num = 0


    def _set_look_east_movement(self: "Enemy", units :int):
        '''Takes units of movement and sets the necessary attributes
           for a look east movement.'''
        if self._current_look_num <= units:
            self.image = pygame.image.load("boo_east0.png")
            self._looking_east = True
            self._current_look_num += 1
        else:
            self._instr_index += 1
            self._looking_east = False
            self._current_look_num = 0


    def _set_look_west_movement(self: "Enemy", units :int):
        '''Takes units of movement and sets the necessary attributes
           for a look west movement.'''
        if self._current_look_num <= units:
            self.image = pygame.image.load("boo_west0.png")
            self._looking_west = True
            self._current_look_num += 1
        else:
            self._instr_index += 1
            self._looking_west = False
            self._current_look_num = 0


    def _set_wait_movement(self: "Enemy", units: int):
        '''Takes units of movement and sets the necessary attributes
           for a wait movement.'''
        if self._current_wait_num <= units:
            self._current_wait_num += 1
        else:
            self._instr_index += 1
            self._current_wait_num = 0


    def _set_go_east_movement(self: "Enemy", units: int):
        '''Takes units of movement and sets the necessary attributes
           for an eastward movement.'''
        if self._current_step_num <= units:
            self._is_moving = True
            self._looking_east = True
            self.rect.x += self.patrol_speed
            self._current_step_num += 1
        else:
            self._is_moving = False
            self._looking_east = False
            self._instr_index += 1 #increment self._instr_index here
            self._current_step_num = 0 #reset the number of steps for an instruction
                

    def _set_go_west_movement(self: "Enemy", units: int):
        '''Takes units of movement and sets the necessary attributes
           for a westward movement.'''
        if self._current_step_num <= units:
            self._is_moving = True
            self._looking_west = True
            self.rect.x -= self.patrol_speed
            self._current_step_num += 1
        else:
            self._is_moving = False
            self._looking_west = False
            self._instr_index += 1 
            self._current_step_num = 0


    def _set_go_north_movement(self: "Enemy", units: int):
        '''Takes units of movement and sets the necessary attributes
           for a northward movement.'''
        if self._current_step_num <= units:
            self._is_moving = True
            self._looking_north = True
            self.rect.y -= self.patrol_speed
            self._current_step_num += 1
        else:
            self._is_moving = False
            self._looking_north = False
            self._instr_index += 1
            self._current_step_num = 0

    
    def _set_go_south_movement(self: "Enemy", units: int):
        '''Takes units of movement and sets ets the necessary attributes
           for a southward movement.'''
        if self._current_step_num <= units:
            self._is_moving = True
            self._looking_south = True
            self.rect.y += self.patrol_speed
            self._current_step_num += 1
        else:
            self._is_moving = False
            self._looking_south = False
            self._instr_index += 1
            self._current_step_num = 0

    
    def _animate(self: "Enemy", image_lst: [str]):
        '''Steps through an animation corresponding to the provided list of images.'''
        if self._cur_frame < 2:
            self._cur_frame += 1
            self.image = pygame.image.load(image_lst[self._cur_frame])
        elif self._cur_frame == 2:
            self._cur_frame = 0
            self.image = pygame.image.load(image_lst[self._cur_frame])
