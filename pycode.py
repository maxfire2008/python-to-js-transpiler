number_1 = input("Input a number:")

nw_l = int(number_1)
nw_c = nw_l

print(nw_l)

for i in range(10):
    print(nw_c)
    nw_w = nw_c
    nw_c = nw_c + nw_l
    nw_l = nw_w
