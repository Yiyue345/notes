const VISITOR_COUNTED_AT_KEY = 'notes-analytics:visitor-counted-at';
export const VISITOR_COUNT_WINDOW_MS = 24 * 60 * 60 * 1_000;

interface AnalyticsWindow extends Window {
	__notesAnalyticsLastPageView?: string;
}

interface SiteVisitReservation {
	shouldCount: boolean;
	marker?: string;
}

export function isVisitorCountWindowActive(value: string | null, now = Date.now()) {
	if (!value) return false;
	const countedAt = Number(value);
	return Number.isFinite(countedAt)
		&& countedAt >= 0
		&& countedAt <= now
		&& now - countedAt < VISITOR_COUNT_WINDOW_MS;
}

function reserveSiteVisit(now = Date.now()): SiteVisitReservation {
	try {
		const countedAt = window.localStorage.getItem(VISITOR_COUNTED_AT_KEY);
		if (isVisitorCountWindowActive(countedAt, now)) {
			return { shouldCount: false };
		}

		const marker = String(now);
		window.localStorage.setItem(VISITOR_COUNTED_AT_KEY, marker);
		return { shouldCount: true, marker };
	} catch {
		return { shouldCount: true };
	}
}

function rollbackSiteVisitReservation(reservation: SiteVisitReservation) {
	if (!reservation.marker) return;
	try {
		if (window.localStorage.getItem(VISITOR_COUNTED_AT_KEY) === reservation.marker) {
			window.localStorage.removeItem(VISITOR_COUNTED_AT_KEY);
		}
	} catch {
		// Nothing to roll back when localStorage is unavailable.
	}
}

function readAnalyticsMeta(name: string) {
	return document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content ?? '';
}

async function recordPageView() {
	const runtimeWindow = window as AnalyticsWindow;
	const path = window.location.pathname;
	if (runtimeWindow.__notesAnalyticsLastPageView === path) return;
	runtimeWindow.__notesAnalyticsLastPageView = path;

	const siteVisit = reserveSiteVisit();
	try {
		const response = await fetch('/api/analytics', {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			credentials: 'same-origin',
			keepalive: true,
			body: JSON.stringify({
				path,
				title: readAnalyticsMeta('notes:analytics-title') || document.title,
				type: readAnalyticsMeta('notes:analytics-type') === 'article' ? 'article' : 'page',
				countSiteVisit: siteVisit.shouldCount,
			}),
		});
		if (!response.ok) rollbackSiteVisitReservation(siteVisit);
	} catch {
		// Analytics must never interrupt page rendering or navigation.
		rollbackSiteVisitReservation(siteVisit);
	}
}

export function initSiteAnalytics() {
	void recordPageView();
}
