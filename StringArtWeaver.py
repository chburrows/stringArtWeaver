from PIL import Image, ImageDraw, ImageEnhance
from fractions import Fraction
import pickle
import numpy as np

class pathCreator:
	def __init__(self, imagePath, numNails=200, maxLines=1500, stringOpacity=35, skipNeighbors=15, shape="circle", showImages=True):
		self.contrast_factor = 1.25

		self.numNails = numNails
		self.totalLines = maxLines
		self.opacity = max(min(stringOpacity, 255), 1)
		self.skipNeighbors = skipNeighbors
		self.shape = shape
		self.imageName = imagePath
		self.showImages = showImages

		self.loadImage()
		self.createEdges()
		

	def loadImage(self):
		if self.shape == "rectangle":
			self.im = Image.open("images/source/"+self.imageName).convert("L")
			self.pix = self.im.load()
		elif self.shape == "circle":
			img = Image.open("images/source/"+self.imageName).convert("L")

			contrast = ImageEnhance.Contrast(img)
			img = contrast.enhance(self.contrast_factor)

			w,h = img.size
			s = min(w,h)
			img = img.crop((w//2-s//2, h//2-s//2, w//2+s//2, h//2+s//2)) # crop to square centered on middle of image

			white_img = Image.new('L', (s,s), 255)
			mask_img = Image.new('L',[s,s] ,0) 
			draw = ImageDraw.Draw(mask_img)
			draw.pieslice([(0,0),(s,s)],0,360,fill=255)
			
			# creating final image
			self.im = Image.composite(img,white_img,mask_img)
			self.pix = self.im.load()

			if self.showImages:
				self.im.show()
			

	def createEdges(self):
		if self.shape == "rectangle":
			imageSize = (self.im.size[0]-1,self.im.size[1]-1)
			numNailsX = round(self.numNails*(imageSize[0]/(imageSize[0]+imageSize[1]))/2)
			numNailsY = round(self.numNails*(1 - imageSize[0]/(imageSize[0]+imageSize[1]))/2)
			spacing = imageSize[0]/numNailsX, imageSize[1]/numNailsY
			self.edges = [(round(spacing[0]*i),0) for i in range(numNailsX)]
			self.edges += [(imageSize[0],round(spacing[1]*i)) for i in range(numNailsY)]
			self.edges += [(round(imageSize[0]-spacing[0]*i),imageSize[1]) for i in range(numNailsX)]
			self.edges += [(0,round(imageSize[1]-spacing[1]*i)) for i in range(numNailsY)]
			self.distances = {(p1,p2):self.distance(p1,p2) for p1 in self.edges for p2 in self.edges}
		
		elif self.shape == "circle":
			edgeX0, edgeY0 = self.im.size[0]/2, self.im.size[1]/2
			xComponentFactor = lambda index: np.cos(index / self.numNails * 2 * np.pi)
			yComponentFactor = lambda index: np.sin(index / self.numNails * 2 * np.pi)
			self.edges = []
			for i in range(self.numNails):
				self.edges.append((round(edgeX0 + (edgeX0 - 1) * xComponentFactor(i)), round(edgeY0 + (edgeY0 - 1) * yComponentFactor(i))))
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
			stepVector = self.getStep(currPt,nextPt,dist)

			currPix = currPt
			intensity = 0
			for s in range(round(dist)):
				intensity += 255-self.pix[currPix]
				currPix = self.addPoint(currPix,stepVector)
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
			self.pix[currPix] = min(255, self.pix[currPix] + self.opacity)
			outputPix[currPix] = (outputPix[currPix][0] - color[0],outputPix[currPix][1] - color[1],outputPix[currPix][2] - color[2])
			currPix = self.addPoint(currPix,step)

	def generate(self,bgColor=(255,255,255),stringColor=(0,0,0),doOutput=True):
		outImg = Image.new("RGB",self.im.size,color=bgColor)
		outPix = outImg.load()

		invColor = tuple(round(self.opacity/255.0 * (255-x)) for x in stringColor)

		currIndex = 0
		self.points = [self.edges[currIndex]]
		self.path = []
		percentFinished = 0
		self.repeatedPts = 0
		for i in range(self.totalLines):
			if self.repeatedPts > 10 and doOutput:
				self.totalLines = i
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
		if self.showImages:
			outImg.show()
		outImg.save("images/output/"+''.join(self.imageName.split('.')[:-1])+"-out.png")
		if doOutput:
			print("Wrote output to images/output/" +''.join(self.imageName.split('.')[:-1])+"-out.png")
	def savePath(self, num):
		thisObj = {
		"imageName" : self.imageName,
		"numNails" : self.numNails,
		"totalLines" : self.totalLines,
		"opacity" : self.opacity,
		"skipNeighbors" : self.skipNeighbors,
		"shape": self.shape,
		"path" : self.path,
		"points" : self.points
		}
		with open('saves/'+''.join(self.imageName.split('.')[:-1])+'-save-'+str(num)+'.bin','wb') as f:
			pickle.dump(thisObj,f)
	def distance(self,pt1,pt2):
		return ((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2 )**0.5
	def getStep(self,currPt,nextPt,size):
		return((nextPt[0]-currPt[0])/size,(nextPt[1]-currPt[1])/size)
	def addPoint(self,pt1,pt2):
		return (pt1[0]+pt2[0],pt1[1]+pt2[1])
class loadedPath:
	def __init__(self,fName,totalLines=None, stringOpacity=None, showImages=True):
		with open('saves/'+fName,'rb') as f:
			o = pickle.load(f)
		lines = o['totalLines'] if totalLines==None or totalLines > o['totalLines'] else totalLines
		opacity = o['stringOpacity'] if stringOpacity==None else stringOpacity
		self.pc = pathCreator(o['imageName'],o['numNails'],lines,opacity,o['skipNeighbors'], shape=o['shape'],showImages=showImages)
		self.path = o['path'][:lines]
		self.points = o['points'][:lines]
		self.shape = o['shape']
		self.fName = fName
		self.showImages = showImages
	def drawImage(self, bgColor=(255,255,255),stringColor=(0,0,0)): #TODO: make these two funcs below work with circle
		outImg = Image.new("RGB",self.pc.im.size,color=bgColor)
		outImgPix = outImg.load()
		invColor = tuple(round(self.pc.opacity/255.0 * (255-x)) for x in stringColor)
		for i in range(len(self.points)-1):
			cp = self.points[i]
			np = self.points[i+1]
			self.pc.drawNext(outImgPix,invColor,cp,np)
		outImg.save("images/output/"+self.fName+"-out.png")
		if self.showImages:
			outImg.show()
	def showPath(self, startIndex=0, numOutput=5):
		aspRatio = Fraction(self.pc.im.size[0],self.pc.im.size[1]).limit_denominator(100)
		nailsX = len([x for x in self.pc.edges if x[1] == 0])
		nailsY = len([x for x in self.pc.edges if x[0] == 0])
		print("Aspect Ratio: %d:%d\nNumber of nails on top side(total): %d\nNumber of nails on left side(total): %d\n" % (aspRatio.numerator, aspRatio.denominator,nailsX,nailsY))
		# for i in range(startIndex,len(self.path)):
		# 	cp = self.path[i][0]
		# 	np = self.path[i][1]
		# 	print("Line %d: %d -> %d" % (i+1,cp,np))
		# 	if (i + 1) % numOutput == 0:
		# 		input()

		with open("results.txt","w") as f:
			perRow = 2
			for i in range(startIndex,len(self.path), numOutput * perRow):
				cols = []
				for l in range(perRow):
					cols.append(" ".join("{:>3}".format(str(self.path[j][0])) for j in range(i+l*numOutput,min(i+(l+1)*numOutput,len(self.path)))))
				result_line = f"{' '*3}|{' '*3}".join(cols)
				
				print(result_line)
				f.write(result_line+"\n")
			