import StringArtWeaver

def createImg(imgPath, saveNum):
    numNails = 292
    maxLines = 10000
    stringOpacity = 25 # 1 - 255 (255 is opaque)
    skipNeighbors = 2
    shape = "circle"
    
    bgColor = (240, 230, 221)
    stringColor = (158, 141, 106)

    pc = StringArtWeaver.pathCreator(imgPath, numNails, maxLines, stringOpacity, skipNeighbors, shape)
    pc.generate(bgColor,stringColor)
    pc.savePath(saveNum)

def loadImg(loadPath):
    PAGE = 48 * 20
    maxLines = int(PAGE * 4)
    stringOpacity = 25 # 1 - 255 (255 is opaque)

    bgColor = (255,255,255)
    stringColor = (0,0,0)

    lp = StringArtWeaver.loadedPath(loadPath,maxLines,stringOpacity)
    lp.drawImage(bgColor,stringColor)
    #lp.showPath(numOutput=10)

#createImg("IMG_7156_crop.jpg", 3)
loadImg("IMG_7156_crop-save-3.bin")