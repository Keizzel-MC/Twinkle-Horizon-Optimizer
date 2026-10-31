//! Standalone no-dependency Rust harness, compiling the EXACT native helper
//! files with lightweight representations of pinned Horizon private types.
//! `cargo test` here does NOT replace cargo check against the full Horizon game.
#![forbid(unsafe_code)]

pub mod gfx {
    pub mod page_runs {
        #[derive(Clone, Copy, Debug, PartialEq, Eq)]
        pub struct Run {
            key: u64,
            start: u32,
            len: u32,
            tag: [u32; 3],
        }

        #[derive(Clone, Default)]
        pub struct PageRuns {
            runs: Vec<Run>,
            scratch: Vec<([u32; 5], (u32, Option<u32>))>,
        }

        include!("../../native/twinkle_opt/mixins/twinkle_opt/page_runs_already_sorted.rs");

        impl PageRuns {
            fn original<'a>(
                &'a mut self,
                draws: &mut [[u32; 5]],
                pages: &mut [(u32, Option<u32>)],
                base: usize,
            ) -> &'a [Run] {
                // Directly modeled after Horizon aa27eca / gfx/page_runs.rs (MIT).
                let page = |r: &Run| r.key as u32;
                if self.runs.windows(2).all(|w| page(&w[0]) == page(&w[1])) {
                    return &self.runs;
                }
                self.runs.sort_by_key(|r| r.key);
                self.scratch.clear();
                for r in &mut self.runs {
                    let (s, e) = (r.start as usize, (r.start + r.len) as usize);
                    r.start = (base + self.scratch.len()) as u32;
                    self.scratch
                        .extend(draws[s..e].iter().copied().zip(pages[s..e].iter().copied()));
                }
                for (i, &(draw, p)) in self.scratch.iter().enumerate() {
                    draws[base + i] = draw;
                    pages[base + i] = p;
                }
                &self.runs
            }
        }

        #[cfg(test)]
        mod tests {
            use super::*;
            fn sample(keys: &[u64], lens: &[usize], prefix: usize) -> (
                PageRuns, Vec<[u32; 5]>, Vec<(u32, Option<u32>)>
            ) {
                let mut a = PageRuns::default();
                let mut draws = vec![[123; 5]; prefix];
                let mut pages = vec![(321, Some(7)); prefix];
                for (&key, &len) in keys.iter().zip(lens) {
                    let first = draws.len();
                    let id = a.runs.len() as u32;
                    a.runs.push(Run {
                        key, start: first as u32, len: len as u32, tag: [id, 3, 9],
                    });
                    for j in 0..len {
                        draws.push([id, j as u32, 3, 4, 5]);
                        pages.push((key as u32, Some(j as u32)));
                    }
                }
                draws.extend([[222; 5]; 4]);
                pages.extend([(322, Some(8)); 4]);
                (a, draws, pages)
            }
            fn run(keys: &[u64], lens: &[usize], prefix: usize) {
                let (mut old, mut od, mut op) = sample(keys, lens, prefix);
                let (mut new, mut nd, mut np) = sample(keys, lens, prefix);
                let a = old.original(&mut od, &mut op, prefix).to_vec();
                let b = page_runs_already_sorted(&mut new, &mut nd, &mut np, prefix).to_vec();
                assert_eq!(a, b);
                assert_eq!(od, nd);
                assert_eq!(op, np);
            }
            #[test]
            fn cases() {
                for keys in [
                    vec![], vec![1], vec![2, 1, 2, 1],
                    vec![1, 2, 3, 3, 3], vec![(3u64 << 32) | 4, (1u64 << 32) | 4],
                    vec![u64::MAX, 0, u64::MAX],
                ] {
                    let lens = vec![3; keys.len()];
                    run(&keys, &lens, 5);
                }
            }
            #[test]
            fn pseudo_random_2000() {
                let mut seed = 0x9e3779b97f4a7c15_u64;
                for case in 0..2000 {
                    let len = case % 35;
                    let mut keys = Vec::new();
                    let mut lens = Vec::new();
                    for _ in 0..len {
                        seed ^= seed << 13;
                        seed ^= seed >> 7;
                        seed ^= seed << 17;
                        keys.push(if case % 2 == 0 { seed % 20 } else { seed });
                        lens.push(1 + ((seed >> 12) % 6) as usize);
                    }
                    if case % 3 == 0 { keys.sort(); }
                    run(&keys, &lens, case % 7);
                }
            }
        }
    }

    pub mod resident {
        #[derive(Clone, Debug)]
        pub struct Column {
            sections: Vec<(i32, u32)>,
            low: i32,
            high: i32,
        }
        include!("../../native/twinkle_opt/mixins/twinkle_opt/column_bounds_one_pass.rs");

        #[cfg(test)]
        mod tests {
            use super::*;
            #[test]
            fn bounds_2000() {
                let mut seed: u32 = 173;
                for n in 0..2000 {
                    let mut c = Column { sections: Vec::new(), low: 0, high: 0 };
                    for i in 0..n % 83 {
                        seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
                        c.sections.push((seed as i32, i as u32));
                    }
                    let old_min = c.sections.iter().map(|s| s.0).min().unwrap_or(0);
                    let old_max = c.sections.iter().map(|s| s.0).max().unwrap_or(0);
                    assert!(matches!(column_bounds_one_pass(&mut c), core::ops::ControlFlow::Break(())));
                    assert_eq!((c.low, c.high), (old_min, old_max));
                }
            }
        }
    }

    pub mod translucency {
        #[derive(Default)]
        pub struct Sorter {
            order: Vec<(u32, f32)>,
            indices: Vec<u32>,
        }
        include!("../../native/twinkle_opt/mixins/twinkle_opt/tiny_translucency_sort.rs");

        impl Sorter {
            fn original(&mut self, centers: &[[f32; 3]], camera: [f32; 3]) -> &[u32] {
                self.order.clear();
                self.order.extend(centers.iter().enumerate().map(|(i, c)| {
                    let [x, y, z] = std::array::from_fn(|j| camera[j] - c[j]);
                    (i as u32, x * x + y * y + z * z)
                }));
                self.order.sort_by(|a, b| b.1.total_cmp(&a.1));
                self.indices.clear();
                for &(quad, _) in &self.order {
                    let v = quad * 4;
                    self.indices.extend([v, v + 1, v + 2, v + 2, v + 3, v]);
                }
                &self.indices
            }
        }

        #[cfg(test)]
        mod tests {
            use super::*;
            fn compare(centers: &[[f32; 3]], camera: [f32; 3]) {
                let mut a = Sorter::default();
                let mut b = Sorter::default();
                assert_eq!(a.original(centers, camera), tiny_translucency_sort(&mut b, centers, camera));
                assert_eq!(
                    a.order.iter().map(|(i, d)| (*i, d.to_bits())).collect::<Vec<_>>(),
                    b.order.iter().map(|(i, d)| (*i, d.to_bits())).collect::<Vec<_>>()
                );
            }
            #[test]
            fn ties_inf_and_nan() {
                for a in [0.0, -0.0, f32::INFINITY, f32::NEG_INFINITY, f32::NAN] {
                    for b in [0.0, -0.0, f32::INFINITY, f32::NEG_INFINITY, f32::NAN] {
                        compare(&[[a, 0.0, 1.0], [b, 0.0, 1.0]], [0.0; 3]);
                    }
                }
            }
            #[test]
            fn pseudo_random_2000_and_fallback() {
                let mut seed = 0x12345678_u32;
                for case in 0..2000 {
                    let count = case % 8;
                    let mut centers = Vec::new();
                    for _ in 0..count {
                        let mut xyz = [0f32; 3];
                        for val in &mut xyz {
                            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
                            *val = (seed as i32 as f32) / 131072.0;
                        }
                        centers.push(xyz);
                    }
                    compare(&centers, [10.0, 1.5, -40.0]);
                }
            }
        }
    }
}
