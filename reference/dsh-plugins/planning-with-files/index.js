// planning-with-files — 明月技能 dsh 插件(自动生成)
// Cordis 标准插件形态: 只做最小注册,不访问注入属性
export const name = '@deepseek-ai/dsh-skill-planning-with-files';
export const config = { skill: "planning-with-files", source: 'skills/planning-with-files/SKILL.md' };

export function apply(ctx) {
  // 极简: 插件加载成功即注册完成(避免 cordis inject 限制)
  return { skill: config.skill, source: config.source };
}
