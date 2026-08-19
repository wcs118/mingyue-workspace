// shushu-internship — 明月技能 dsh 插件(自动生成)
// Cordis 标准插件形态: 只做最小注册,不访问注入属性
export const name = '@deepseek-ai/dsh-skill-shushu-internship';
export const config = { skill: "shushu-internship", source: 'skills/shushu-internship/SKILL.md' };

export function apply(ctx) {
  // 极简: 插件加载成功即注册完成(避免 cordis inject 限制)
  return { skill: config.skill, source: config.source };
}
