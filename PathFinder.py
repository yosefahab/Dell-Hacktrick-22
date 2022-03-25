import sys
 
class Cell  :
    def __init__(self, x, y, dist, prev) :
        self.x = x
        self.y = y
        self.dist = dist; #distance to start
        self.prev = prev; #parent cell in the path
 
    def __str__(self):
        return "("+ str(self.x) + "," + str(self.y) + ")" 
        
    def toTuple(self):
        return (self.x, self.y)
    

class PathFinder :
    """ Get the shortest path between cells with BFS """
    #BFS, Time O(n^2), Space O(n^2)

    def shortestPath(self, matrix, start, end) :
        sx = start[0]
        sy = start[1]
        dx = end[0]
        dy = end[1]
		
		#initialize the cells 
        m = len(matrix)
        n = len(matrix[0])    
        cells = []
        for i in range (0, m) :
            row = []
            for j in range(0, n) :               
                if matrix[i][j] != 0 :
                    row.append(Cell(i, j, sys.maxsize, None))
                else:
                    row.append(None)
            cells.append(row) 
        
	    #breadth first search
        queue = []     
        src = cells[sx][sy]
        src.dist = 0
        queue.append(src)
        dest = None
        p = queue.pop(0)
        while p != None :
	    	#find destination 
            if p.x == dx and p.y == dy : 
                dest = p
                break	   
	        # moving up
            self.visit(cells, queue, p.x-1, p.y, p)    
            # moving left
            self.visit(cells, queue, p.x, p.y-1, p)     
	        # moving down
            self.visit(cells, queue, p.x+1, p.y, p)             
	        #moving right
            self.visit(cells, queue, p.x, p.y+1, p)
            if len(queue) > 0:
                p = queue.pop(0)
            else:
                p = None       
 
	    #compose the path if path exists
        if dest == None :
            print("there is no path.")
            return
        else :
            path = []
            p = dest
            while p != None :
                path.insert(0, p)	      
                p = p.prev	       
            retList = list()
            for c in path:
                retList.append(Cell.toTuple(c))
            
            return retList
	
 
	#function to update cell visiting status, Time O(1), Space O(1)
    def visit(self, cells, queue, x, y, parent) :		
        #out of boundary
        if x < 0 or x >= len(cells) or y < 0 or y >= len(cells[0]) or cells[x][y] == None:
            return
 
	    #update distance, and previous node
        dist = parent.dist + 1
        p = cells[x][y]
        if dist < p.dist :
            p.dist = dist
            p.prev = parent
            queue.append(p)
 
