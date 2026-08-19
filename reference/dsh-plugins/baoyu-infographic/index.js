// baoyu-infographic — 明月技能 dsh 插件(自动生成)
// Cordis 标准插件形态: 只做最小注册,不访问注入属性
export const name = '@deepseek-ai/dsh-skill-baoyu-infographic';
export const config = { skill: "baoyu-infographic", source: 'skills/baoyu-infographic/SKILL.md' };

export function apply(ctx) {
  // 极简: 插件加载成功即注册完成(避免 cordis inject 限制)
  return { skill: config.skill, source: config.source };
}
