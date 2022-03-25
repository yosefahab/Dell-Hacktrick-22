from hacktrick_ai.src.hacktrick_ai_py.mdp.hacktrick_mdp import HacktrickGridworld
from hacktrick_ai.src.hacktrick_ai_py.mdp.actions import Action
from PathFinder import PathFinder


LAYOUT = 'final_collaborative'
class AgentHelper:
    current_order = []

    def __init__(self, player_number):
        self.player_number = player_number
        self.layout = LAYOUT
        self.gridWorld = HacktrickGridworld.from_layout_name(LAYOUT)
        self.pf = PathFinder()
        self._init_ingredients()
        self.set_waiting_factor()
        self.collected_item = []
        self.initial_order = 5
        self.current_order_number = 5
        self.labs_count = 0
        
    def _init_grid(self):
        """ Initialize the game grid according to the layout """
        grid_size = 7
        self.grid = [[1 for i in range(grid_size)] for j in range(grid_size)]
        self.grid[2][5] = 0
        # Set zero to the items' position
        for items in self.item_positions.values():
            for item in items():
                self.grid[item[0]][item[1]] = 0
            
    def _init_ingredients(self):
        self.item_positions = {
            'P' : lambda: self.gridWorld.get_projector_dispenser_locations(),
            'S' : lambda: self.gridWorld.get_solar_cell_dispenser_locations(),
            'L' : lambda: self.gridWorld.get_laptop_dispenser_locations(),
            'CONS' : lambda: self.gridWorld.get_construction_site_locations(),
            'CONT' : lambda: self.gridWorld.get_container_dispenser_locations(),
            'D' : lambda: self.gridWorld.get_serving_locations(),
            'COUNTER' : lambda: self.gridWorld.get_counter_locations()
        }
        self._init_grid()
        self.ingredients = {
            'P' : Ingredient(self.item_positions['P'], self.pf, self.get_standing_point, self.grid),
            'S' : Ingredient(self.item_positions['S'], self.pf, self.get_standing_point, self.grid),
            'L' : Ingredient(self.item_positions['L'], self.pf, self.get_standing_point, self.grid),
            'CONS' : Ingredient(self.item_positions['CONS'], self.pf, self.get_standing_point, self.grid),
            'CONT' : Ingredient(self.item_positions['CONT'], self.pf, self.get_standing_point, self.grid),
            'D' : Ingredient(self.item_positions['D'], self.pf, self.get_standing_point, self.grid),
            'COUNTER' : Ingredient(self.item_positions['COUNTER'], self.pf, self.get_standing_point, self.grid)
        }
    
    def init_orders(self, state):
        """ Initialize the ingredients needed for each order """
        self.orders_time = [10, 15, 20, 20, 30]
        self.orders = []
        for order in state.all_orders:
            ingredients = []
            for ing in order:
                ingredients.append(ing.replace('laptop', 'L').replace('solar_cell', 'S').replace('projector', 'P'))
            
            self.orders.append(ingredients)
        self.cook_new_order(self.initial_order)
        
    def set_waiting_factor(self):
        if self.layout == 'round_of_16_single':
            self.waiting_factor = 4
            self.cooked_labs = 16
            self.last_lab = 2
        elif self.layout == 'quarter_final_single' or self.layout == 'quarter_final_collaborative':
            self.waiting_factor = 50
            self.cooked_labs = 15
            self.last_lab = 4
        elif self.layout in ['semi_final_single', 'final_single']:
            self.waiting_factor = 7
            self.cooked_labs = 13
            self.last_lab = 4
        elif self.layout == 'final_collaborative':
            self.waiting_factor = 4
            self.cooked_labs = 14
            self.last_lab = 2
        else:
            self.waiting_factor = 5
            self.cooked_labs = 16
            self.last_lab = 2

    def cook_new_order(self, order_number):
        """ Set the needed ingredients for the new order """
        self.current_order = list(self.orders[order_number-1])

    def set_player_positions(self, state):
        """ Get the current position of each player """
        self.player_positions = [] 
        for player in state.player_positions:
            self.player_positions.append(player)

    def _cooking_state(self, state):
        return self.gridWorld.get_construction_site_states(state)
    
    def order_is_ready(self, state):
        """ Return True when the order is ready """
        return 'ready' in self._cooking_state(state).keys()
    
    def waiting_to_ready(self, state):
        """ Return True when the agent wait in front of the construction to get the ready order """
        object_held = state.players[self.player_number].held_object
        held_cont = False
        if object_held is not None:
            held_cont = (object_held.name == 'container')
            
        return (not self.order_is_ready(state) and self.order_under_cooking(state) and self.player_positions[self.player_number] == self.get_standing_point(self.player_positions[self.player_number], self.ingredients['CONS'].current_positions[0]) and held_cont)

    def order_under_cooking(self, state):
        """ Return True when the order is under cooking """
        return 'cooking' in self._cooking_state(state).keys()

    def get_standing_point(self, start, point):
        """ Find the suitable position agent must stand on to get items from dispenser """
        x, y = point[0], point[1]

        if x == 6: x -= 1
        elif x == 0: x += 1

        if y == 6: y -= 1
        elif y == 0: y += 1
        
        if x != point[0] or y != point[1]: return x, y

        if start[1] < y and self.grid[x][y-1]:
            y -= 1
        elif start[1] > y and self.grid[x][y+1]:
            y += 1
        elif start[0] > x and self.grid[x+1][y]:
            x += 1
        elif start[0] < x and self.grid[x-1][y]:
            x -= 1

        if x != point[0] or y != point[1]: return x, y

        if self.grid[x][y-1]:
            y-=1
        elif self.grid[x][y+1]:
            y+=1
        elif self.grid[x+1][y]:
            x += 1
        elif self.grid[x-1][y]:
            x-=1
        
        return x, y
        

    def arrage_orientations(self, action_list, stand_point, end):
        """ Change the orientation of the robot to intercat with an item """
        if len(action_list) == 0:
            orient = (0, 0)
        else:
            orient = action_list[-1] 
        action = None 
        
        if stand_point[0] > end[0] and orient != (-1, 0):
            action = (-1, 0)
        elif stand_point[0] < end[0] and orient != (1, 0):
            action = (1, 0)
        elif stand_point[1] > end[1] and orient != (0, -1):
            action = (0, -1)
        elif stand_point[1] < end[1] and orient != (0, 1):
            action = (0, 1) 

        if action is not None:
            action_list.append(action)

        return action_list

    def get_actions(self, start, end):
        """ Calculate wanted actions to reach the destination """
        if end is None:
            return [Action.STAY]
            
        # if self.layout[-6:] != 'single':
        #     grid = list(self.grid)
        #     player_pos = self.player_positions[not self.player_number]
        #     grid[player_pos[0]][player_pos[1]] = 0
        #     points = self.pf.shortestPath(grid, start, self.get_standing_point(start, end))
        # else:
        points = self.pf.shortestPath(self.grid, start, self.get_standing_point(start, end))

        action_list = []

        if points == None:
            return [Action.STAY]
        else:
            for i in range(len(points)-1):
                action_list.append(tuple([points[i+1][0]-points[i][0], points[i+1][1]-points[i][1]]))
            
            action_list = self.arrage_orientations(action_list, self.get_standing_point(start, end), end)
            
            action_list.append(Action.INTERACT)
            return action_list
    
    def avoid_collision(self, action):
        """ Avoid collision between agents """
        if self.layout[-6:] != 'single':
            p1x, p1y = self.player_positions[self.player_number][0], self.player_positions[self.player_number][1]
            p2x, p2y = self.player_positions[not self.player_number][0], self.player_positions[not self.player_number][1]

            if action == 'interact':
                return action
            elif p1x + action[0] == p2x and p1y + action[1] == p2y:
                return Action.STAY
            else:
                return action                
        else:
            return action
        

    def nearest_ingredient(self):
        """ Get the nearest ingredient needed for the current order """
        min_step = 10000
        item_position = (-1, -1)
        item_type = ''

        for ingredient in self.current_order:
            item, steps = self.ingredients[ingredient].nearest_one(self.player_positions[self.player_number])

            if steps < min_step:
                min_step = steps
                item_position = item
                item_type = ingredient

        if item_type == '':
            return None, None

        self.ingredients[item_type].pop(item_position)
        self.current_order.remove(item_type)
        
        if [item_type, item_position] in self.collected_item:
            self.collected_item.remove([item_type, item_position])

        return item_position, min_step
    
    def farthest_ingredient(self):
        """ Get the farthest ingredient needed for the current order """
        max_step = 0
        item_position = (-1, -1)
        item_type = ''

        for ingredient in self.current_order:
            item, steps = self.ingredients[ingredient].farthest_one(self.player_positions[self.player_number])

            if steps > max_step:
                max_step = steps
                item_position = item
                item_type = ingredient
        
        self.ingredients[item_type].pop(item_position)
        self.current_order.remove(item_type)
        return item_position, max_step, item_type

    def decide(self, state, agent_tasks, current_cooking_time, actions):
        """ Make the decision to the robot movement """
        if len(actions) == 0: 
            
            item_position = None
            if len(agent_tasks) == 0:
                # Create new the order ingredients
                if len(self.current_order) == 0 and not self.order_is_ready(state):
                    self.cook_new_order(self.current_order_number)
                    self.current_order = list(set(self.current_order))
                    actions +=  [Action.INTERACT]

                if current_cooking_time > 0 or len(actions) > 0:
                    # Make some items near the construction site for the next order
                    if self.ingredients['CONT'].nearest_one(self.player_positions[self.player_number])[1] * self.waiting_factor  < self.orders_time[self.current_order_number-1] - current_cooking_time and len(self.current_order):
                        item_position, steps, item_type = self.farthest_ingredient()
                        actions += self.get_actions(self.player_positions[self.player_number], item_position)
                        agent_tasks += ['COUNTER'+item_type]
                    
                    # Take the order to the delivery site
                    else:
                        self.labs_count += 1
                        agent_tasks += ['CONT', 'CONS', 'D']

                        if self.labs_count == self.cooked_labs:
                            self.current_order_number = self.last_lab

                        self.cook_new_order(self.current_order_number)

                        # Add previsously collected item 
                        for item in self.collected_item:
                            self.ingredients[item[0]].add(item[1])
                        
                        # Call decide again if actions list wash empty
                        if actions == []:
                            actions = self.decide(state, agent_tasks, current_cooking_time, actions)

                    # print(actions, agent_tasks, self.current_order, self.player_number)
                    return actions
                
                # Find the nearest ingredient
                item_position, steps = self.nearest_ingredient()
                agent_tasks.append('CONS')

            # Already have tasks   
            else:
                if agent_tasks[0][:7] == 'COUNTER':
                    item_position, steps = self.ingredients[agent_tasks[0][:7]].nearest_one(self.construction_stand_point, isCounter=True, collected_item=self.collected_item)
                    self.collected_item.append([agent_tasks[0][7:], item_position])
                else:
                    item_position, steps = self.ingredients[agent_tasks[0]].nearest_one(self.player_positions[self.player_number], isConstruction=(agent_tasks[0] == 'CONS'))
                    
                    # Store construction stand point
                    if agent_tasks[0] == 'CONS':
                        self.construction_stand_point = self.get_standing_point(self.player_positions[self.player_number], item_position)

                agent_tasks.pop(0)

            # Get the actions needed to fetch the ingredient
            actions += self.get_actions(self.player_positions[self.player_number], item_position)
            
            # print(actions, agent_tasks, self.current_order, self.player_number)
        return actions





class Ingredient:
    def __init__(self, dispenser_locations, pathFinder, get_standing, grid):
        self.pathFinder = pathFinder
        self.get_standing_point = get_standing
        self.grid = grid
        self.dispensers = dispenser_locations()
        self.current_positions = list(self.dispensers)

    def shortest_path(self, player_position, ingredient_position, in_steps=False):
        """ Find the shortest path between player and a specific ingredient """
        points = self.pathFinder.shortestPath(self.grid, player_position, self.get_standing_point(player_position, ingredient_position))

        if points is None:
            return 10000000

        if in_steps:
            return len(points)-1
        else:
            return points

    def nearest_one(self, player_position, isConstruction=False, isCounter=False,  collected_item=[]):
        """ Find the nearest item to the player """
        if isConstruction:
            return self.current_positions[0], 0

        min_steps = 10000
        item_position = (-1, -1)
        
        for item in self.current_positions:
            if not item in [(0,0), (6,6), (0, 6), (6, 0), (3,3)]:
                steps = self.shortest_path(player_position, item, True)

                if not isCounter or (isCounter and not (item in self.arrange_collected_item(collected_item))):
                    if steps < min_steps:
                        min_steps = steps
                        item_position = item

        return item_position, min_steps
    
    def arrange_collected_item(self, collected_item):
        collected = []
        for item in collected_item:
            collected.append(item[1])
        return collected
    
    def farthest_one(self, player_position):
        """ Find the farthest item to the player """
        max_steps = -1
        item_position = (-1, -1)

        for item in self.current_positions:
            steps = self.shortest_path(player_position, item, True)
            if steps > max_steps:
                max_steps = steps
                item_position = item

        return item_position, max_steps
    
    def pop(self, item_position):
        """ Remove specific item from the current list, without removing the dispensers """
        if not item_position in self.dispensers:
            self.current_positions.remove(item_position)

    def add(self, item_position):
        """ Add new item to the current list """
        self.current_positions.append(item_position)