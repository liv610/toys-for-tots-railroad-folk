from world import *
import cv2, numpy as np
im=np.full((900,1600,3),235,np.uint8)
def P(a): return [np.round(np.asarray(a)*4).astype(np.int32)]
cv2.fillPoly(im,P(land(FAR,600)),(200,180,170),cv2.LINE_AA,2)
cv2.fillPoly(im,P(land(MID,600)),(170,160,140),cv2.LINE_AA,2)
cv2.fillPoly(im,P(land(RIDGE_L,640)),(90,120,80),cv2.LINE_AA,2)
cv2.fillPoly(im,P(land(RIDGE_R,640)),(90,120,80),cv2.LINE_AA,2)
cv2.fillPoly(im,P(land(VALLEY)),(140,190,160),cv2.LINE_AA,2)
cols=[(120,180,140),(110,170,150),(80,170,200),(100,160,120),(130,200,150),(90,180,190),(70,140,100),(70,140,100)]
for h,c in zip(HILLS,cols):
    cv2.fillPoly(im,P(land(h['top'])),c,cv2.LINE_AA,2); cv2.polylines(im,P(h['top']),False,(40,60,40),1,cv2.LINE_AA,2)
cv2.polylines(im,P(RIVER),False,(200,120,60),6,cv2.LINE_AA,2)
cv2.polylines(im,P(RAIL),False,(30,30,30),2,cv2.LINE_AA,2)
for b in VILLAGE+FARM: cv2.circle(im,(int(b['x']),int(b['y'])),6,(40,40,200),-1)
for t in TREES: cv2.circle(im,(int(t[0]),int(t[1])),3,(20,90,20),-1)
cv2.circle(im,(int(RAIL[BRIDGE_I][0]),int(RAIL[BRIDGE_I][1])),8,(0,0,0),2)
cv2.imwrite('out/layout.png',im)
