// Based on Horizon gfx/page_runs.rs (MIT, Ludovic Marie and contributors).
// Reimplements the exact method with one additional no-copy sorted-key path.
// Exact source SHA and revision enforced by source-lock.json.
fn page_runs_already_sorted<'a>(
    runs: &'a mut crate::gfx::page_runs::PageRuns,
    draws: &mut [[u32; 5]],
    pages: &mut [(u32, Option<u32>)],
    base: usize,
) -> &'a [crate::gfx::page_runs::Run] {
    let page = |r: &crate::gfx::page_runs::Run| r.key as u32;
    // Original shortcut: all entries use the same arena page.
    if runs.runs.windows(2).all(|w| page(&w[0]) == page(&w[1])) {
        return &runs.runs;
    }
    // Additional shortcut: already sorted by full (distance band, page) key.
    // A stable sort would not change runs, starts, draws or pages here.
    if runs.runs.windows(2).all(|w| w[0].key <= w[1].key) {
        return &runs.runs;
    }
    // Original stable-sort and scratch-copy implementation for every other input.
    runs.runs.sort_by_key(|r| r.key);
    runs.scratch.clear();
    for r in &mut runs.runs {
        let (s, e) = (r.start as usize, (r.start + r.len) as usize);
        r.start = (base + runs.scratch.len()) as u32;
        runs.scratch
            .extend(draws[s..e].iter().copied().zip(pages[s..e].iter().copied()));
    }
    for (i, &(draw, p)) in runs.scratch.iter().enumerate() {
        draws[base + i] = draw;
        pages[base + i] = p;
    }
    &runs.runs
}
