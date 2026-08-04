import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import GithubSlugger from 'github-slugger';

const MARKDOWN_EXTENSIONS = new Set(['.md', '.mdx']);
const IMAGE_EXTENSIONS = new Set([
	'.avif',
	'.gif',
	'.jpeg',
	'.jpg',
	'.png',
	'.svg',
	'.webp',
]);

function isInside(root, target) {
	const relative = path.relative(root, target);
	return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function collectFiles(root, predicate, result = []) {
	if (!root || !fs.existsSync(root)) return result;

	for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
		const absolutePath = path.join(root, entry.name);
		if (entry.isDirectory()) {
			collectFiles(absolutePath, predicate, result);
		} else if (predicate(absolutePath)) {
			result.push(absolutePath);
		}
	}

	return result;
}

function slug(value) {
	return new GithubSlugger().slug(value);
}

function routeFromFile(filePath, docsRoot) {
	const relativePath = path.relative(docsRoot, filePath);
	if (!isInside(docsRoot, filePath)) return null;

	const parts = relativePath.replace(/\\/g, '/').replace(/\.(?:md|mdx)$/i, '').split('/');
	if (parts.at(-1)?.toLowerCase() === 'index') parts.pop();

	const route = parts.filter(Boolean).map((part) => slug(part)).join('/');
	return route ? `/${route}/` : '/';
}

function buildIndex(docsRoot, assetRoots) {
	const notes = collectFiles(docsRoot, (filePath) => MARKDOWN_EXTENSIONS.has(path.extname(filePath).toLowerCase()));
	const noteByPath = new Map();
	const notesByName = new Map();

	for (const filePath of notes) {
		const normalizedPath = path.normalize(filePath).toLowerCase();
		noteByPath.set(normalizedPath, filePath);

		const name = path.basename(filePath, path.extname(filePath)).toLowerCase();
		const matches = notesByName.get(name) ?? [];
		matches.push(filePath);
		notesByName.set(name, matches);
	}

	const assets = assetRoots.flatMap((root) => collectFiles(root, (filePath) => IMAGE_EXTENSIONS.has(path.extname(filePath).toLowerCase())));
	const assetsByName = new Map();
	for (const filePath of assets) {
		const name = path.basename(filePath).toLowerCase();
		const matches = assetsByName.get(name) ?? [];
		matches.push(filePath);
		assetsByName.set(name, matches);
	}

	return { noteByPath, notesByName, assetsByName };
}

function decodeLinkPart(value) {
	try {
		return decodeURIComponent(value);
	} catch {
		return value;
	}
}

function splitTarget(value) {
	const hashIndex = value.indexOf('#');
	if (hashIndex === -1) return { pathname: value, fragment: '' };

	return {
		pathname: value.slice(0, hashIndex),
		fragment: value.slice(hashIndex + 1),
	};
}

function markdownCandidates(candidatePath) {
	const extension = path.extname(candidatePath).toLowerCase();
	if (MARKDOWN_EXTENSIONS.has(extension)) return [candidatePath];

	return [
		`${candidatePath}.md`,
		`${candidatePath}.mdx`,
		path.join(candidatePath, 'index.md'),
		path.join(candidatePath, 'index.mdx'),
	];
}

function findExistingNote(candidatePath, docsRoot, index) {
	for (const candidate of markdownCandidates(candidatePath)) {
		if (!isInside(docsRoot, candidate)) continue;
		const indexedPath = index.noteByPath.get(path.normalize(candidate).toLowerCase());
		if (indexedPath) return indexedPath;
		if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
	}

	return null;
}

function nearestMatch(matches, currentFile) {
	if (matches.length === 1) return matches[0];

	const currentDirectory = path.dirname(currentFile);
	return [...matches].sort((left, right) => {
		const leftDistance = path.relative(currentDirectory, left).split(path.sep).length;
		const rightDistance = path.relative(currentDirectory, right).split(path.sep).length;
		return leftDistance - rightDistance || left.localeCompare(right, 'zh-CN');
	})[0];
}

function resolveNote(pathname, currentFile, docsRoot, index) {
	const decodedPath = decodeLinkPart(pathname).replace(/\\/g, '/');
	if (!decodedPath) return currentFile;

	const withoutLeadingSlash = decodedPath.replace(/^\/+/, '');
	const explicitCandidates = decodedPath.startsWith('/')
		? [path.resolve(docsRoot, withoutLeadingSlash)]
		: [
			path.resolve(path.dirname(currentFile), decodedPath),
			path.resolve(docsRoot, withoutLeadingSlash),
		];

	for (const candidate of explicitCandidates) {
		const note = findExistingNote(candidate, docsRoot, index);
		if (note) return note;
	}

	const fileName = path.basename(decodedPath, path.extname(decodedPath)).toLowerCase();
	const matches = index.notesByName.get(fileName);
	return matches?.length ? nearestMatch(matches, currentFile) : null;
}

function fragmentToHash(fragment) {
	if (!fragment) return '';

	const decodedFragment = decodeLinkPart(fragment).replace(/^#+/, '');
	if (!decodedFragment) return '';
	if (decodedFragment.startsWith('^')) return `#${decodedFragment.slice(1)}`;

	const heading = decodedFragment.split('#').filter(Boolean).at(-1) ?? decodedFragment;
	return `#${slug(heading)}`;
}

function resolveNoteUrl(rawUrl, currentFile, docsRoot, index) {
	const { pathname, fragment } = splitTarget(rawUrl);
	const note = resolveNote(pathname, currentFile, docsRoot, index);
	if (!note) return null;

	const route = routeFromFile(note, docsRoot);
	return route ? `${route}${fragmentToHash(fragment)}` : null;
}

function findAliasSeparator(value) {
	for (let index = 0; index < value.length; index += 1) {
		if (value[index] === '|' && value[index - 1] !== '\\') return index;
	}
	return -1;
}

function splitWikiTarget(value) {
	const separator = findAliasSeparator(value);
	if (separator === -1) return { target: value.trim(), alias: '' };

	return {
		target: value.slice(0, separator).trim(),
		alias: value.slice(separator + 1).trim().replace(/\\\|/g, '|'),
	};
}

function resolveAsset(target, currentFile, assetRoots, publicRoot, index) {
	const decodedTarget = decodeLinkPart(splitTarget(target).pathname).replace(/\\/g, '/');
	if (!IMAGE_EXTENSIONS.has(path.extname(decodedTarget).toLowerCase())) return null;

	const withoutLeadingSlash = decodedTarget.replace(/^\/+/, '');
	const candidates = [
		path.resolve(path.dirname(currentFile), decodedTarget),
		...assetRoots.map((root) => path.resolve(root, withoutLeadingSlash)),
	];

	let asset = candidates.find((candidate) => fs.existsSync(candidate) && fs.statSync(candidate).isFile());
	if (!asset) {
		const matches = index.assetsByName.get(path.basename(decodedTarget).toLowerCase());
		asset = matches?.length ? nearestMatch(matches, currentFile) : null;
	}
	if (!asset) return null;

	if (publicRoot && isInside(publicRoot, asset)) {
		return `/${path.relative(publicRoot, asset).replace(/\\/g, '/')}`;
	}

	let relativePath = path.relative(path.dirname(currentFile), asset).replace(/\\/g, '/');
	if (!relativePath.startsWith('.')) relativePath = `./${relativePath}`;
	return relativePath;
}

function imageDimensions(alias) {
	const match = /^(\d+)(?:x(\d+))?$/.exec(alias);
	if (!match) return null;
	return { width: Number(match[1]), ...(match[2] ? { height: Number(match[2]) } : {}) };
}

function wikiNode(match, embedded, value, currentFile, options, index, file) {
	const { target, alias } = splitWikiTarget(value);

	if (embedded) {
		const url = resolveAsset(target, currentFile, options.assetRoots, options.publicRoot, index);
		if (!url) return { type: 'text', value: match };

		const dimensions = imageDimensions(alias);
		return {
			type: 'image',
			url,
			alt: dimensions ? path.basename(splitTarget(target).pathname, path.extname(target)) : alias || path.basename(target),
			...(dimensions ? { data: { hProperties: dimensions } } : {}),
		};
	}

	const url = resolveNoteUrl(target, currentFile, options.docsRoot, index);
	if (!url) {
		file.message(`无法解析 Obsidian 内部链接：${match}`);
		return { type: 'text', value: match };
	}

	return {
		type: 'link',
		url,
		children: [{ type: 'text', value: alias || target.replace(/\.(?:md|mdx)$/i, '') }],
	};
}

function transformTextNode(node, currentFile, options, index, file) {
	const pattern = /(!)?\[\[([^\]\n]+)\]\]/g;
	const children = [];
	let cursor = 0;

	for (const match of node.value.matchAll(pattern)) {
		if (match.index > 0 && node.value[match.index - 1] === '\\') continue;
		if (match.index > cursor) children.push({ type: 'text', value: node.value.slice(cursor, match.index) });
		children.push(wikiNode(match[0], Boolean(match[1]), match[2], currentFile, options, index, file));
		cursor = match.index + match[0].length;
	}

	if (cursor === 0) return null;
	if (cursor < node.value.length) children.push({ type: 'text', value: node.value.slice(cursor) });
	return children;
}

function shouldTryMarkdownLink(url) {
	if (!url || url.startsWith('#') || url.startsWith('//')) return false;
	if (/^[a-z][a-z\d+.-]*:/i.test(url)) return false;

	const { pathname } = splitTarget(url);
	const extension = path.extname(decodeLinkPart(pathname)).toLowerCase();
	return extension === '' || MARKDOWN_EXTENSIONS.has(extension);
}

function transformChildren(parent, currentFile, options, index, file) {
	if (!Array.isArray(parent.children)) return;

	for (let childIndex = 0; childIndex < parent.children.length; childIndex += 1) {
		const child = parent.children[childIndex];

		if (child.type === 'link' && shouldTryMarkdownLink(child.url)) {
			const resolvedUrl = resolveNoteUrl(child.url, currentFile, options.docsRoot, index);
			if (resolvedUrl) {
				child.url = resolvedUrl;
			} else if (/\.(?:md|mdx)(?:#|$)/i.test(child.url)) {
				file.message(`无法解析 Obsidian Markdown 链接：${child.url}`);
			}
			continue;
		}

		if (child.type === 'text') {
			const replacement = transformTextNode(child, currentFile, options, index, file);
			if (replacement) {
				parent.children.splice(childIndex, 1, ...replacement);
				childIndex += replacement.length - 1;
			}
			continue;
		}

		if (!['code', 'inlineCode', 'html', 'image'].includes(child.type)) {
			transformChildren(child, currentFile, options, index, file);
		}
	}
}

function vfilePath(file) {
	const value = String(file.path ?? '');
	if (!value) return null;
	return value.startsWith('file:') ? fileURLToPath(value) : path.resolve(value);
}

export function remarkObsidianLinks(userOptions = {}) {
	const projectRoot = path.resolve(userOptions.projectRoot ?? process.cwd());
	const docsRoot = path.resolve(projectRoot, userOptions.docsRoot ?? 'src/content/docs');
	const publicRoot = path.resolve(projectRoot, userOptions.publicRoot ?? 'public');
	const assetRoots = (userOptions.assetRoots ?? ['src/content/docs', 'src/assets', 'public']).map((root) => path.resolve(projectRoot, root));
	let index = buildIndex(docsRoot, assetRoots);

	return (tree, file) => {
		const currentFile = vfilePath(file);
		if (!currentFile || !isInside(docsRoot, currentFile)) return;

		// Refresh when a newly created Obsidian note is compiled by the dev server.
		if (!index.noteByPath.has(path.normalize(currentFile).toLowerCase())) {
			index = buildIndex(docsRoot, assetRoots);
		}

		transformChildren(tree, currentFile, { docsRoot, publicRoot, assetRoots }, index, file);
	};
}
