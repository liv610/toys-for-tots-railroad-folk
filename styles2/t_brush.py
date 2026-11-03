from brush import *
import time
c=Canvas(1200,700,2,'#efe4cc')
t=time.time()
m=c.area([(30,60),(260,40),(280,200),(40,230)],'#6f8f5a',seed=1)
c.flow_fill(m,lambda x,y:0.1,lambda x,y,r:mix('#6f8f5a','#a3b07a',r.rand()*.6),9,60,7,dry=.35,seed=2)
for i in range(8):
    c.stroke([(320,40+i*28),(420,30+i*28),(560,50+i*28)],14,'#c46a4a',dry=i/8)
c.ink([(30,280),(120,300),(250,270),(380,320)],1.6)
for i in range(60):
    c.dab(400+ (i%10)*14, 250+(i//10)*12, 14, 6, 0.4*i, ['#4f6f4a','#7c9a5c','#2f4d3d'][i%3])
print(time.time()-t)
c.save('out/t_brush')
