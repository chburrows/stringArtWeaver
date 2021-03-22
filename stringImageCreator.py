from PIL import Image
import pickle, sys

class pathCreator:
	def __init__(self, imagePath, numNails=200, maxLines=1500, stringThickness=35, skipNeighbors=15):
		self.numNails = numNails
		self.totalLines = maxLines
		self.stringThickness = stringThickness
		self.skipNeighbors = skipNeighbors
		
		self.loadImage(imagePath)
		

	def loadImage(self,imagePath):
		self.imageName = imagePath
		self.im = Image.open("images/source/"+self.imageName).convert("L")
		self.pix = self.im.load()

		self.createEdges()

	def createEdges(self):
		imageSize = (self.im.size[0]-1,self.im.size[1]-1)
		numNailsX = round(self.numNails*(imageSize[0]/(imageSize[0]+imageSize[1]))/2)
		numNailsY = round(self.numNails*(1 - imageSize[0]/(imageSize[0]+imageSize[1]))/2)
		spacing = imageSize[0]/numNailsX, imageSize[1]/numNailsY
		self.edges = [(round(spacing[0]*i),0) for i in range(numNailsX)]
		self.edges += [(imageSize[0],round(spacing[1]*i)) for i in range(numNailsY)]
		self.edges += [(round(imageSize[0]-spacing[0]*i),imageSize[1]) for i in range(numNailsX)]
		self.edges += [(0,round(imageSize[1]-spacing[1]*i)) for i in range(numNailsY)]
		self.distances = {(p1,p2):self.distance(p1,p2) for p1 in self.edges for p2 in self.edges}
	
	def getNext(self,currIndex):
		currPt = self.edges[currIndex]
		maxPt = (currIndex,0)
		for j in range(1+self.skipNeighbors,len(self.edges)-self.skipNeighbors):
			nextIndex = (currIndex + j) % len(self.edges)
			nextPt = self.edges[nextIndex]
			if nextPt == self.edges[currIndex]:
				continue
			dist = self.distances[currPt,nextPt]
			step = self.getStep(currPt,nextPt,dist)

			currPix = currPt
			intensity = 0
			for s in range(round(dist)):
				intensity += 255-self.pix[currPix]
				currPix = self.addPoint(currPix,step)
			intensity = intensity/dist
			if(intensity > maxPt[1]):
				maxPt = (nextIndex,intensity)
		return maxPt[0]
	def drawNext(self,outputPix,color,fromPt, toPt):
		if fromPt == toPt:
			self.repeatedPts += 1
			return None

		dist = self.distances[fromPt,toPt]
		step = self.getStep(fromPt,toPt,dist)

		currPix = fromPt
		for s in range(round(dist)):
			self.pix[currPix] = min(255, self.pix[currPix] + self.stringThickness)
			outputPix[currPix] = (outputPix[currPix][0] - color[0],outputPix[currPix][1] - color[1],outputPix[currPix][2] - color[2])
			currPix = self.addPoint(currPix,step)

	def generate(self,bgColor=(255,255,255),stringColor=(0,0,0),doOutput=True):
		outImg = Image.new("RGB",self.im.size,color=bgColor)
		outPix = outImg.load()

		invColor = tuple(round(self.stringThickness/255.0 * (255-x)) for x in stringColor)

		self.points = []
		self.path = []
		currIndex = 0
		percentFinished = 0
		self.repeatedPts = 0
		for i in range(self.totalLines):
			if self.repeatedPts > 10 and doOutput:
				print("Stopped generating after %d lines because the image is complete" % (i+1))
				break

			nextIndex = self.getNext(currIndex)
			self.drawNext(outPix, invColor, self.edges[currIndex],self.edges[nextIndex])

			self.path.append((currIndex,nextIndex))
			self.points.append(self.edges[nextIndex])

			if doOutput and round(i/self.totalLines*100) != percentFinished:
				percentFinished = round(i/self.totalLines*100)
				print("%d%% done: %d -> %d" % (percentFinished,currIndex,nextIndex))

			currIndex = nextIndex
		outImg.save("images/output/"+self.imageName.split('.')[0]+"-out.png")
		if doOutput:
			print("Wrote output to images/output/" +self.imageName.split('.')[0]+"-out.png")
	def savePath(self, num):
		thisObj = {
		"imageName" : self.imageName,
		"numNails" : self.numNails,
		"totalLines" : self.totalLines,
		"stringThickness" : self.stringThickness,
		"skipNeighbors" : self.skipNeighbors,
		"path" : self.path,
		"points" : self.points
		}
		with open('saves/'+self.imageName.split('.')[0]+'-save-'+str(num)+'.bin','wb') as f:
			pickle.dump(thisObj,f)
	def distance(self,pt1,pt2):
		return ((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2 )**0.5
	def getStep(self,currPt,nextPt,size):
		return((nextPt[0]-currPt[0])/size,(nextPt[1]-currPt[1])/size)
	def addPoint(self,pt1,pt2):
		return (pt1[0]+pt2[0],pt1[1]+pt2[1])
class loadedPath:
	def __init__(self,fName,totalLines=None, stringThickness=None):
		with open('saves/'+fName+'.bin','rb') as f:
			o = pickle.load(f)
		lines = o['totalLines'] if totalLines==None or totalLines > o['totalLines'] else totalLines
		thickness = o['stringThickness'] if stringThickness==None else stringThickness
		self.pc = pathCreator(o['imageName'],o['numNails'],lines,thickness,o['skipNeighbors'])
		self.path = o['path'][:lines]
		self.points = o['points'][:lines]
		self.fName = fName
	def drawImage(self, bgColor=(255,255,255),stringColor=(0,0,0)):
		outImg = Image.new("RGB",self.pc.im.size,color=bgColor)
		outImgPix = outImg.load()
		invColor = tuple(round(self.pc.stringThickness/255.0 * (255-x)) for x in stringColor)
		for i in range(len(self.points)-1):
			cp = self.points[i]
			np = self.points[i+1]
			self.pc.drawNext(outImgPix,invColor,cp,np)
		outImg.save("images/output/"+self.fName+"-out.png")
	def showPath(self, startIndex=0, numOutput=5):
		for i in range(startIndex,len(self.path)):
			cp = self.path[i][0]
			np = self.path[i][1]
			print("Line %d: %d -> %d" % (i+1,cp,np))
			if (i + 1) % numOutput == 0:
				input()


if __name__ == '__main__':
	name = "leaf"
	num = 5
	load = False

	numNails = 100
	maxLines = 500
	thickness = 40
	skipNeighbors = 0

	bgColor = (255,255,255)
	stringColor = (0,0,0)

	doOutput = True
	if not load:
		pc = pathCreator(name + ".jpg", numNails, maxLines, thickness, skipNeighbors)
		pc.generate(bgColor,stringColor)
		pc.savePath(num)
	else:
		lp = loadedPath(name+'-save-'+str(num),maxLines,thickness)
		lp.drawImage(bgColor,stringColor)
		lp.showPath()
