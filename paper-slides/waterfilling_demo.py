"""
论文《LLM Agent 工作流延迟-可靠性-成本权衡》注水分配（Water-Filling）示例
=====================================================================

大白话理解：
我们有 N 个 LLM Agent 串起来干活，每个 Agent 的"大β"（beta）不一样。
- β 大 → 给一点点 token 就很快变靠谱（效率高）
- β 小 → 给很多 token 才慢慢变靠谱（效率低）

问题：总共只有 B 个 token 可用，怎么分给每个 Agent 才能让整体最靠谱？
答案：注水分配——β 小的多分点，β 大的少分点，直到所有 Agent 最后 1 个 token 带来的"靠谱提升"都一样。
"""

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 第0步：参数设定
# ============================================================

# 假设有 5 个 LLM Agent
N = 5

# 每个 Agent 的 β 值（越大表示"给点 token 就快速变靠谱"）
# 单位是 1/token
betas = np.array([0.001, 0.002, 0.0005, 0.003, 0.0015])

# 为了方便，也给每个 Agent 的 α 和推理 token 设一些值
# （用户成本只跟输出 token 有关，推理 token 这里固定）
alphas = np.array([0.001, 0.001, 0.001, 0.001, 0.001])
X_values = np.array([500, 500, 500, 500, 500])  # 推理 token（固定）

# 总 token 预算（输出 token 总数上限）
budget = 12000

print(f"{'='*60}")
print(f"📋 场景设定")
print(f"{'='*60}")
print(f"Agent 数量: {N}")
print(f"每个 Agent 的 β (效率参数): {betas}")
print(f"  注：β 越大 → 给一点 token 就能变靠谱")
print(f"  注：β 越小 → 需要很多 token 才慢慢变靠谱")
print(f"总 token 预算: {budget}")
print()

# ============================================================
# 第1步：注水分配实现
# ============================================================

def waterfilling_allocation(betas, budget, tol=1e-8, max_iter=1000):
    """
    注水分配算法
    
    公式：L_j = (1/β_j) * log(1 + β_j / θ)
    
    用二分法找 θ，使得 sum(L_j) = budget
    
    参数含义：
    - θ：影子价格。越大表示 token 越稀缺，大家分到的越少
    - L_j: Agent j 分到的 token 数
    """
    
    # θ 的搜索范围：从很小到很大
    theta_low = 1e-10
    theta_high = 1e5
    
    for _ in range(max_iter):
        theta_mid = (theta_low + theta_high) / 2
        
        # 按公式计算分配
        L = np.maximum(0, (1.0 / betas) * np.log(1.0 + betas / theta_mid))
        
        total = np.sum(L)
        
        if abs(total - budget) < tol:
            break
        
        if total > budget:
            theta_low = theta_mid       # θ 太小，分太多，需要调大 θ
        else:
            theta_high = theta_mid      # θ 太大，分太少，需要调小 θ
    
    return L, theta_mid


def uniform_allocation(betas, budget):
    """均匀分配：每个 Agent 拿一样多"""
    return np.full_like(betas, budget / len(betas))


def proportional_allocation(betas, budget):
    """按 β 正比分配：β 大的分更多"""
    total_beta = np.sum(betas)
    return (betas / total_beta) * budget


def inverse_proportional_allocation(betas, budget):
    """按 β 反比分配：β 小的分更多（感知上接近注水）"""
    inv_betas = 1.0 / betas
    total_inv = np.sum(inv_betas)
    return (inv_betas / total_inv) * budget


# 计算各种分配
L_water, theta_opt = waterfilling_allocation(betas, budget)
L_uniform = uniform_allocation(betas, budget)
L_proportional = proportional_allocation(betas, budget)
L_inverse = inverse_proportional_allocation(betas, budget)

print(f"{'='*60}")
print(f"📊 分配结果对比")
print(f"{'='*60}")
print(f"{'Agent':>8} | {'β':>8} | {'注水分配':>10} | {'均匀':>8} | {'正比β':>8} | {'反比β':>8}")
print(f"{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}")
for i in range(N):
    print(f"{i+1:>8.0f} | {betas[i]:>8.5f} | {L_water[i]:>10.1f} | {L_uniform[i]:>8.1f} | {L_proportional[i]:>8.1f} | {L_inverse[i]:>8.1f}")
print(f"{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}")
print(f"{'合计':>8} | {'':>8} | {np.sum(L_water):>10.1f} | {np.sum(L_uniform):>8.1f} | {np.sum(L_proportional):>8.1f} | {np.sum(L_inverse):>8.1f}")
print()

print(f"📌 最优影子价格 θ = {theta_opt:.6f}")
print()


# ============================================================
# 第2步：验证"边际收益拉平"原理
# ============================================================

def marginal_benefit(L_j, beta_j):
    """
    边际收益：多给 1 个 token 对 log(可靠性) 的提升
    
    公式：d/dL log(1 - e^{-βL}) = β * e^{-βL} / (1 - e^{-βL})
    """
    exp_term = np.exp(-beta_j * L_j)
    return beta_j * exp_term / (1 - exp_term)


print(f"{'='*60}")
print(f"🔍 验证「边际收益拉平」原理")
print(f"{'='*60}")
print(f"注水分配下，所有活跃 Agent 的最后 1 个 token 带来的")
print(f"log-可靠性提升应该都等于影子价格 θ = {theta_opt:.6f}")
print()

margins = []
for i in range(N):
    if L_water[i] > 0:
        mb = marginal_benefit(L_water[i], betas[i])
        margins.append(mb)
        print(f"  Agent {i+1} (β={betas[i]:.5f}): 分到 {L_water[i]:>10.1f} token, 边际收益 = {mb:.6f}")
    else:
        print(f"  Agent {i+1} (β={betas[i]:.5f}): 分到 {L_water[i]:>10.1f} token (未激活)")

print()


# ============================================================
# 第3步：可靠性计算对比
# ============================================================

def reliability(L_j, alpha_j, X_j, beta_j):
    """Agent 的可靠性：ρ = (1 - e^{-αX}) * (1 - e^{-βL})"""
    return (1 - np.exp(-alpha_j * X_j)) * (1 - np.exp(-beta_j * L_j))


def workflow_reliability(L_vec, alphas, X_vec, betas):
    """工作流可靠性 = 各 Agent 可靠性相乘"""
    rels = np.array([reliability(L_vec[i], alphas[i], X_vec[i], betas[i]) for i in range(len(L_vec))])
    return np.prod(rels), rels


print(f"{'='*60}")
print(f"📈 各策略的工作流整体可靠性")
print(f"{'='*60}")

strategies = {
    "注水分配(最优)": L_water,
    "均匀分配": L_uniform,
    "正比β分配": L_proportional,
    "反比β分配": L_inverse,
}

for name, L in strategies.items():
    r_total, r_agents = workflow_reliability(L, alphas, X_values, betas)
    print(f"\n  {name}:")
    print(f"    工作流整体可靠性 = {r_total:.6f} ({r_total*100:.2f}%)")
    for i in range(N):
        print(f"      Agent {i+1} 可靠性 = {r_agents[i]:.6f} ({r_agents[i]*100:.2f}%)")
print()


# ============================================================
# 第4步：形象化理解——包子和胃口
# ============================================================

print(f"{'='*60}")
print(f"🍔 包子类比：理解注水分配")
print(f"{'='*60}")
print(f"""
你有 12000 个「包子」(token)，要喂给 5 个不同胃口的人（Agent）：
""")

for i in range(N):
    # 用通俗方式描述 β：需要多少个包子才能达到 80% 饱
    need_80pct = -np.log(0.2) / betas[i]
    need_50pct = -np.log(0.5) / betas[i]
    
    if betas[i] == max(betas):
        desc = "小胃口🍚"
    elif betas[i] == min(betas):
        desc = "大胃口🍱"
    else:
        desc = "中等胃口🍜"
    
    got = L_water[i]
    
    print(f"  人{i+1} ({desc}, β={betas[i]:.5f}):")
    print(f"    吃 {need_50pct:.0f} 个包子就半饱，吃 {need_80pct:.0f} 个就 80% 饱")
    print(f"    注水分配给你 {got:.0f} 个包子")
    print()

print(f"注水分配的原则是：")
print(f"  最后 1 个包子，每个人吃下去获得「满足感」都一样。")
print(f"  胃口大的人（β 小）要多分点，胃口小的人（β 大）少分点。")
print(f"  均匀分包子反而是浪费——小胃口的人吃撑了，大胃口的人还没饱。")
print()


# ============================================================
# 第5步：可视化
# ============================================================

# 准备画图
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ---- 图1：分配对比柱状图 ----
ax1 = axes[0, 0]
x = np.arange(N)
width = 0.2

ax1.bar(x - 1.5*width, L_uniform, width, label='均匀', color='#999999')
ax1.bar(x - 0.5*width, L_proportional, width, label='正比β', color='#66b3ff')
ax1.bar(x + 0.5*width, L_inverse, width, label='反比β', color='#ffcc99')
ax1.bar(x + 1.5*width, L_water, width, label='注水(最优)', color='#ff6b6b')

ax1.set_xlabel('Agent')
ax1.set_ylabel('分配 Token 数')
ax1.set_title('不同策略的 Token 分配对比')
ax1.set_xticks(x)
ax1.set_xticklabels([f'Agent {i+1}\nβ={betas[i]:.4f}' for i in range(N)])
ax1.legend()

# ---- 图2：单个 Agent 的可靠性曲线 + 分配点 ----
ax2 = axes[0, 1]
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']

L_range = np.linspace(0, 5000, 1000)
for i in range(N):
    rel = 1 - np.exp(-betas[i] * L_range)
    # 先乘以固定推理部分
    fixed_part = 1 - np.exp(-alphas[i] * X_values[i])
    rel_total = fixed_part * rel
    ax2.plot(L_range, rel_total, label=f'Agent {i+1} (β={betas[i]:.4f})', 
             color=colors[i], linewidth=1.5)
    # 标注注水分配点
    ax2.scatter(L_water[i], reliability(L_water[i], alphas[i], X_values[i], betas[i]), 
                color=colors[i], s=100, zorder=5, marker='o')

ax2.set_xlabel('输出 Token 数 (L)')
ax2.set_ylabel('Agent 可靠性')
ax2.set_title('各 Agent 可靠性 vs. Token 投入\n(● = 注水分配位置)')
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

# ---- 图3：边际收益拉平 ----
ax3 = axes[1, 0]

# 画边际收益曲线
for i in range(N):
    margins_curve = marginal_benefit(L_range, betas[i])
    ax3.plot(L_range, margins_curve, label=f'Agent {i+1} (β={betas[i]:.4f})', 
             color=colors[i], linewidth=1.5)
    # 标注注水分配点
    if L_water[i] > 0:
        mb = marginal_benefit(L_water[i], betas[i])
        ax3.scatter(L_water[i], mb, color=colors[i], s=100, zorder=5, marker='s')
        ax3.axhline(y=mb, xmin=0, xmax=L_water[i]/5500, color=colors[i], linestyle='--', alpha=0.4, linewidth=1)

# 标注 θ 水平线
ax3.axhline(y=theta_opt, color='red', linestyle='-', linewidth=2, alpha=0.7, label=f'影子价格 θ={theta_opt:.5f}')

ax3.set_xlabel('输出 Token 数 (L)')
ax3.set_ylabel('边际收益\n(d(logρ)/dL)')
ax3.set_title('注水分配拉平了所有 Agent 的边际收益\n(■ = 分配点，红=θ)')
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

# ---- 图4：不同预算下工作流可靠性对比 ----
ax4 = axes[1, 1]

budgets = np.linspace(1000, 20000, 50)

water_reliabilities = []
uniform_reliabilities = []
prop_reliabilities = []
inv_prop_reliabilities = []

for B in budgets:
    L_w, _ = waterfilling_allocation(betas, B)
    L_u = uniform_allocation(betas, B)
    L_p = proportional_allocation(betas, B)
    L_ip = inverse_proportional_allocation(betas, B)
    
    water_reliabilities.append(workflow_reliability(L_w, alphas, X_values, betas)[0])
    uniform_reliabilities.append(workflow_reliability(L_u, alphas, X_values, betas)[0])
    prop_reliabilities.append(workflow_reliability(L_p, alphas, X_values, betas)[0])
    inv_prop_reliabilities.append(workflow_reliability(L_ip, alphas, X_values, betas)[0])

ax4.plot(budgets, water_reliabilities, label='注水(最优)', color='#ff6b6b', linewidth=2.5)
ax4.plot(budgets, uniform_reliabilities, label='均匀', color='#999999', linewidth=2, linestyle='--')
ax4.plot(budgets, prop_reliabilities, label='正比β', color='#66b3ff', linewidth=2, linestyle='--')
ax4.plot(budgets, inv_prop_reliabilities, label='反比β', color='#ffcc99', linewidth=2, linestyle='--')

ax4.set_xlabel('总 Token 预算 (B)')
ax4.set_ylabel('工作流整体可靠性')
ax4.set_title('不同预算下各策略的可靠性对比')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('waterfilling_demo.png', dpi=120)
print(f"📊 图表已保存到 waterfilling_demo.png")
print()


# ============================================================
# 第6步：交互式小工具——手动尝试分配
# ============================================================

print(f"{'='*60}")
print(f"🎮 交互小实验：你来当分配师")
print(f"{'='*60}")
print(f"""
手动分配 {budget} 个 token 给 5 个 Agent，看看你的方案和最优方案差多少。
（在下面代码中修改 manual_allocation 数组即可试不同方案）
""")

# 手动尝试：把下面的数字改成你想要的
manual_allocation = np.array([3000, 2000, 3500, 1500, 2000])

r_manual, _ = workflow_reliability(manual_allocation, alphas, X_values, betas)
r_opt, _ = workflow_reliability(L_water, alphas, X_values, betas)

print(f"  你的方案: {manual_allocation}")
print(f"  合计: {np.sum(manual_allocation)} token")
print(f"  工作流可靠性: {r_manual*100:.2f}%")
print(f"  最优方案可靠性: {r_opt*100:.2f}%")
print(f"  差距: {(r_opt - r_manual)*100:.2f} 个百分点")
print()

# 提示
print(f"{'='*60}")
print(f"💡 给你的分配建议")
print(f"{'='*60}")
print(f"""
你想让整体最靠谱？记住三个原则：

1️⃣ β 小的多分，β 大的少分
   Agent 3 (β最小=0.0005) 需要最多 token ({L_water[2]:.0f})
   Agent 4 (β最大=0.003) 只需要最少 token ({L_water[3]:.0f})

2️⃣ 最后 1 个 token 应该投给谁？投给边际收益最高的那个。
   等所有 Agent 的边际收益一样时，就是最优了。

3️⃣ 均匀分配几乎总是次优的
   只有所有 Agent 的 β 完全一样时，均匀才最优。
""")
