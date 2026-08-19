import assert from 'node:assert/strict';
import test from 'node:test';
import { onRequestGet, onRequestPost } from '../edge-functions/api/analytics.js';

class MemoryBlob {
	values = new Map();

	async get(key, options = {}) {
		const value = this.values.get(key) ?? null;
		return value !== null && options.type === 'json' ? JSON.parse(value) : value;
	}

	async setJSON(key, value) {
		this.values.set(key, JSON.stringify(value));
	}

	async list({ prefix = '' } = {}) {
		return {
			blobs: [...this.values.keys()]
				.filter((key) => key.startsWith(prefix))
				.sort()
				.map((key) => ({ key })),
		};
	}
}

function createContext(store, request) {
	return { request, analyticsStore: store };
}

function createVisitRequest(body, headers = {}) {
	return new Request('https://notes.yiyuemeow.com/api/analytics', {
		method: 'POST',
		headers: { 'content-type': 'application/json', ...headers },
		body: JSON.stringify(body),
	});
}

test('records article views, site visits, and recent visit time', async () => {
	const store = new MemoryBlob();
	const articlePath = new URL('https://notes.yiyuemeow.com/math/概率论/参数估计/').pathname;
	const request = createVisitRequest({
		path: articlePath,
		title: '参数估计',
		type: 'article',
		countSiteVisit: true,
	});
	const response = await onRequestPost(createContext(store, request));
	const payload = await response.json();

	assert.equal(response.status, 200);
	assert.equal(payload.site.totalVisits, 1);
	assert.match(payload.site.lastVisitedAt, /^\d{4}-\d{2}-\d{2}T/);
	assert.deepEqual(
		{ path: payload.article.path, title: payload.article.title, views: payload.article.views },
		{ path: articlePath, title: '参数估计', views: 1 },
	);
});

test('skips a duplicate site visit while still counting article views', async () => {
	const store = new MemoryBlob();
	const body = { path: '/article/', title: 'Article', type: 'article' };
	await onRequestPost(createContext(store, createVisitRequest({ ...body, countSiteVisit: true })));
	const response = await onRequestPost(
		createContext(store, createVisitRequest({ ...body, countSiteVisit: false })),
	);
	const payload = await response.json();

	assert.equal(payload.site.totalVisits, 1);
	assert.equal(payload.article.views, 2);
});

test('counts directory and home pages only in site statistics', async () => {
	const store = new MemoryBlob();
	const response = await onRequestPost(
		createContext(store, createVisitRequest({ path: '/math/', title: '数学', type: 'page' })),
	);
	const payload = await response.json();

	assert.equal(payload.site.totalVisits, 1);
	assert.equal(payload.article, null);
	assert.equal([...store.values.keys()].filter((key) => key.startsWith('analytics/articles/')).length, 0);
});

test('returns a limited popular article ranking', async () => {
	const store = new MemoryBlob();
	const visit = async (path, title) => onRequestPost(
		createContext(store, createVisitRequest({ path, title, type: 'article' })),
	);
	await visit('/first/', 'First');
	await visit('/second/', 'Second');
	await visit('/second/', 'Second');

	const response = await onRequestGet(createContext(
		store,
		new Request('https://notes.yiyuemeow.com/api/analytics?limit=1'),
	));
	const payload = await response.json();

	assert.equal(response.status, 200);
	assert.equal(payload.site.totalVisits, 3);
	assert.deepEqual(
		payload.popularArticles.map(({ path, title, views }) => ({ path, title, views })),
		[{ path: '/second/', title: 'Second', views: 2 }],
	);
	assert.deepEqual(payload.meta, { limit: 1, truncated: false, consistency: 'strong' });
});

test('rejects cross-origin writes and invalid payloads', async () => {
	const store = new MemoryBlob();
	const crossOrigin = await onRequestPost(createContext(
		store,
		createVisitRequest(
			{ path: '/', type: 'page' },
			{ origin: 'https://example.com', 'sec-fetch-site': 'cross-site' },
		),
	));
	const invalidType = await onRequestPost(createContext(
		store,
		createVisitRequest({ path: '/article/', type: 'unknown' }),
	));

	assert.equal(crossOrigin.status, 403);
	assert.equal(invalidType.status, 400);
	assert.equal(store.values.size, 0);
});

test('returns 503 when Blob storage is unavailable', async () => {
	const store = new MemoryBlob();
	store.get = async () => { throw new Error('Blob unavailable'); };
	const originalError = console.error;
	console.error = () => undefined;
	try {
		const response = await onRequestGet(createContext(
			store,
			new Request('https://notes.yiyuemeow.com/api/analytics'),
		));
		assert.equal(response.status, 503);
		assert.equal((await response.json()).error.code, 'ANALYTICS_UNAVAILABLE');
	} finally {
		console.error = originalError;
	}
});
