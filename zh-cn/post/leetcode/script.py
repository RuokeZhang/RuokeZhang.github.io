import pandas as pd

# 1. 读取 CSV 文件
df = pd.read_csv('/Users/ruoke/Documents/blog/HomePage/content/zh-cn/post/leetcode/刷穿LeetCode 26ng - Ruoke.csv')

# 2. 筛选 "Need Review" 列为 "Yes" 的行
# 注意：有时候单元格里会有空格，用 str.strip() 去除比较保险
need_review_df = df[df['Need Review'].str.strip() == 'Yes']

# 3. 打印结果
print("需要复习的题目数量:", len(need_review_df))
print(need_review_df[['Question', 'Topic', 'Notes']])  # 只打印题目、主题和笔记

# 4. (可选) 将筛选结果保存为新文件
need_review_df.to_csv('/Users/ruoke/Documents/blog/HomePage/content/zh-cn/post/leetcode/need_review_list.csv', index=False)