from re import L


def sol(nums, target):
    n=len(nums)
    expr=[]
    res=[]
    def backtrack(i, cur_val, start):
        #可以从任意位置开始，任意位置结束，但必须是连续的。加法和乘法同样优先级
        if not start and target==cur_val:
            #可以在任意位置结束
            res.append(''.join(expr))
        if i==n:
            return
        for j in range(i, n):
            if j>i and nums[i]=='0':
                break
            val=int(nums[i:j+1])
            if start:
                #必须放数字，不能放符号
                expr.append(str(val))
                backtrack(j+1, val, False)
                expr.pop()
            else:
                #如果加法和乘法同一优先级
                expr.append('+')
                expr.append(str(val))
                backtrack(j+1, cur_val+val, False)
                expr.pop()
                expr.pop()
                expr.append('*')
                expr.append(str(val))
                backtrack(j+1, cur_val*val, False)
                expr.pop()
                expr.pop()
    for i in range(n):
        #可以从任意位置开始
        backtrack(i, 0, True)
    return res



def find_expressions(nums, target):
    n = len(nums)
    res = []
    expr = []

    def backtrack(i, cur_val, is_first):
        if not is_first and cur_val == target:
            res.append(''.join(expr))
            # 如果只想找一个答案，可以这里 return True
            # 如果想找所有答案，就继续往下搜

        if i == n:
            return

        val = nums[i]

        # 1. 不选当前数字
        backtrack(i + 1, cur_val, is_first)

        # 2. 选当前数字
        if is_first:
            expr.append(str(val))
            backtrack(i + 1, val, False)
            expr.pop()
        else:
            expr.append('+')
            expr.append(str(val))
            backtrack(i + 1, cur_val + val, False)
            expr.pop()
            expr.pop()

            expr.append('*')
            expr.append(str(val))
            backtrack(i + 1, cur_val * val, False)
            expr.pop()
            expr.pop()

    backtrack(0, 0, True)
    return res

nums=[2,1, 0,2, 2,3]
#找subsequence
target=10
def sol(nums, target):
    expr=[]
    res=[]
    n=len(nums)
    def dfs(i, cur_val, is_start):
        if cur_val==target and not is_start:
            res.append(''.join(expr))
            #如果后面全是skip,那么同一个expression可能会被重复加入
        if i==n:
            return
        val=nums[i]
        # choose nums[i]
        if is_start:
            expr.append(str(val))
            dfs(i+1, val, False)
            expr.pop()
        else:
            #需要operation sign
            # + sign
            expr.append('+')
            expr.append(str(val))
            dfs(i+1, val+cur_val, False)
            expr.pop()
            expr.pop()
            # * sign
            expr.append('*')
            expr.append(str(val))
            dfs(i+1, val*cur_val, False)
            expr.pop()
            expr.pop()
        # don't choose nums[i]
        dfs(i+1, cur_val, is_start)
    dfs(0, 0, True)
    return res
print(sol(nums, target))


        


            
            

