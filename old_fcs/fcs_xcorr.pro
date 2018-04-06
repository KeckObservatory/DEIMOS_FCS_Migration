box 1 sc=base+34 sr=0  nc=1180 nr=200
box 2 sc=base+34 sr=0  nc=1180 nr=1
box 3 sc=10      sr=0  nc=190  nr=1

mn   1 box=1 silent
clip 1 box=1 min=1.1*m1
mn   2 box=1 silent
clip 2 box=1 min=1.1*m2

mash 3 1 sp=10,199
mash 5 2 sp=10,199

mash 4 1 col sp=base+34,base+1213
mash 6 2 col sp=base+34,base+1213

cross 7 5 3 box=2 rad=30.0
abx 7 all high_col=xshift silent

box    9 sc=xshift-1 sr=0 nc=3 nr=1
window 7 box=9
poly 7 ord=2 div LOAD
set xpolyfit=-coeff1/(2*coeff2)

cross 8 6 4 box=3 rad=30.0
abx 8 all high_col=yshift silent

box    9 sc=yshift-1 sr=0 nc=3  nr=1
window 8 box=9
poly 8 ord=2 div LOAD
set ypolyfit=-coeff1/(2*coeff2)

! printf 'xshift %i4  yshift %i4' xshift yshift
! printf 'xpolyfit %f11.6 ypolyfit %f11.6' xpolyfit ypolyfit
end
