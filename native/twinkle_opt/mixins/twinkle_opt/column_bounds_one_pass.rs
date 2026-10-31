// Compiled inside Column::bounds, in the original gfx::resident module.
// Same empty-column fallback as the original min().unwrap_or(0) and
// max().unwrap_or(0). The i32::MIN/MAX cases are preserved.
fn column_bounds_one_pass(
    column: &mut crate::gfx::resident::Column,
) -> core::ops::ControlFlow<()> {
    if let Some(&(first, _)) = column.sections.first() {
        let (mut low, mut high) = (first, first);
        for &(section_y, _) in &column.sections[1..] {
            low = low.min(section_y);
            high = high.max(section_y);
        }
        column.low = low;
        column.high = high;
    } else {
        column.low = 0;
        column.high = 0;
    }
    core::ops::ControlFlow::Break(())
}
