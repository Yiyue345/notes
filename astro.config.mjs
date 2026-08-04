// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { unified } from '@astrojs/markdown-remark';
import rehypeKatex from 'rehype-katex';
import rehypeSlug from 'rehype-slug';
import remarkMath from 'remark-math';
import { starlightThemeObsidianConfigSchema } from 'starlight-theme-obsidian/config';
import starlightThemeObsidian from "starlight-theme-obsidian";
import { remarkObsidianLinks } from './src/plugins/remark-obsidian-links.mjs';

// https://astro.build/config
export default defineConfig({
	site: "https://notes.yiyuemeow.com",
	markdown: {
		processor: unified({
			remarkPlugins: [remarkObsidianLinks, remarkMath],
			rehypePlugins: [rehypeSlug, [rehypeKatex, { throwOnError: false, strict: false }]],
		}),
	},
	integrations: [
		starlight({
			title: 'Notes',
			customCss: ['./src/styles/markdown.css'],
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/YiYue345' }],
			defaultLocale: "root",
			locales: {
				root: {
					label: "简体中文",
					lang: "zh-CN"
				}
			},
			plugins: [
				starlightThemeObsidian({
					graph: false,
					backlinks: false,
				}),
			],
			sidebar: [
				{
					label: '数学',
					collapsed: true,
					items: [{ autogenerate: { 
						directory: 'math' ,
						collapsed: true,
					} 
				}],
				},
				{
					label: 'Kotlin 与 Android',
					collapsed: true,
					items: [{ 
						autogenerate: { 
							directory: '至于kotlin' ,
							collapsed: true,
						} 
					}],
				},
				{
					label: 'Flutter',
					collapsed: true,
					items: [{ 
						autogenerate: { 
							directory: '用Flutter让你飞起来！' ,
							collapsed: true,
						} 
					}],
				},
				{
					label: 'C++',
					collapsed: true,
					items: [{ 
						autogenerate: { 
							directory: '看看C艹' ,
							collapsed: true,
						} 
					}],
				},
				{
					label: '杂谈',
					collapsed: true,
					items: [{ 
						autogenerate: { 
							directory: '随便写写' ,
							collapsed: true,
						} 
					}],
				},
				{
					label: '其他',
					collapsed: true,
					items: [
						{ slug: 'to-do-list' },
						{ slug: '这一天天的' },
					],
				},
			],
		}),
	],
});
