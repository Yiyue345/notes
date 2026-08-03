// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { starlightThemeObsidianConfigSchema } from 'starlight-theme-obsidian/config';
import starlightThemeObsidian from "starlight-theme-obsidian";

// https://astro.build/config
export default defineConfig({
	site: "https://notes.yiyuemeow.com",
	integrations: [
		starlight({
			title: 'Ciallo~',
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
					label: 'Guides',
					items: [
						// Each item here is one entry in the navigation menu.
						{ label: 'Example Guide', slug: 'guides/example' },
					],
				},
				{
					label: 'Reference',
					items: [{ autogenerate: { directory: 'reference' } }],
				},
			],
		}),
	],
});
