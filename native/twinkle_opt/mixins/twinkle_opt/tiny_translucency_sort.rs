// Based on Horizon gfx/translucency.rs (MIT, Ludovic Marie and contributors).
// For 0..2 quads, replace stable sort with at most one total_cmp; otherwise
// execute the original exact stable sort. Quad scoring and index order match.
fn tiny_translucency_sort<'a>(
    sorter: &'a mut crate::gfx::translucency::Sorter,
    centers: &[[f32; 3]],
    camera: [f32; 3],
) -> &'a [u32] {
    sorter.order.clear();
    sorter.order.extend(centers.iter().enumerate().map(|(i, c)| {
        let [x, y, z] = std::array::from_fn(|j| camera[j] - c[j]);
        (i as u32, x * x + y * y + z * z)
    }));

    if sorter.order.len() == 2 {
        // Equivalent to stable descending sort, including total order of NaNs.
        if sorter.order[1].1.total_cmp(&sorter.order[0].1).is_gt() {
            sorter.order.swap(0, 1);
        }
    } else if sorter.order.len() > 2 {
        sorter.order.sort_by(|a, b| b.1.total_cmp(&a.1));
    }

    sorter.indices.clear();
    for &(quad, _) in &sorter.order {
        let v = quad * 4;
        sorter.indices.extend([v, v + 1, v + 2, v + 2, v + 3, v]);
    }
    &sorter.indices
}
