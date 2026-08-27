def countt(arr):
    dictt = {}
    for i in arr:
        dictt[i] = dictt.get(i, 0) + 1
    total = 0
    for val in dictt.values():
        total += val // 3
    return total

def roead(arr, S):
    arr.sort()
    L = arr[0]
    R = arr[-1]
    RS = abs(R - S)
    LS = abs(L - S)
    if RS < LS:
        return RS + (R - L)
    else:
        return LS + (R - L)

def blood(arr, x):
    arr.sort()
    o = 0
    t = 0
    for i in arr:
        if o < x:
            t += i
            0 += 1
        else:
            return t
        