from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from textual._resolve import resolve_box_models
from textual.geometry import NULL_OFFSET, Region, Size
from textual.layout import ArrangeResult, Layout, WidgetPlacement

if TYPE_CHECKING:
    from textual.geometry import Spacing
    from textual.widget import Widget


class VerticalLayout(Layout):
    """Used to layout Widgets vertically on screen, from top to bottom."""

    name = "vertical"

    def arrange(
        self, parent: Widget, children: list[Widget], size: Size
    ) -> ArrangeResult:
        placements: list[WidgetPlacement] = []
        add_placement = placements.append
        viewport = parent.app.size

        child_styles = [child.styles for child in children]
        box_margins: list[Spacing] = [
            styles.margin for styles in child_styles if styles.overlay != "screen"
        ]
        if box_margins:
            resolve_margin = Size(
                max(
                    [
                        margin_right + margin_left
                        for _, margin_right, _, margin_left in box_margins
                    ]
                ),
                sum(
                    [
                        bottom if bottom > top else top
                        for (_, _, bottom, _), (top, _, _, _) in zip(
                            box_margins, box_margins[1:]
                        )
                    ]
                )
                + (box_margins[0].top + box_margins[-1].bottom),
            )
        else:
            resolve_margin = Size(0, 0)

        box_models = resolve_box_models(
            [styles.height for styles in child_styles],
            children,
            size,
            parent.app.size,
            resolve_margin,
            resolve_dimension="height",
        )

        margins = [
            (
                margin_bottom
                if (margin_bottom := margin1.bottom) > (margin_top := margin2.top)
                else margin_top
            )
            for (_, _, margin1), (_, _, margin2) in zip(box_models, box_models[1:])
        ]

        if box_models:
            margins.append(box_models[-1].margin.bottom)

        y = next(
            (
                Fraction(box_model.margin.top)
                for box_model, child in zip(box_models, children)
                if child.styles.overlay != "screen"
            ),
            Fraction(0),
        )

        _Region = Region
        _WidgetPlacement = WidgetPlacement
        _Size = Size
        for widget, (content_width, content_height, box_margin), margin in zip(
            children, box_models, margins
        ):
            styles = widget.styles
            has_rule = styles.has_rule
            overlay = styles.overlay == "screen"
            next_y = y + content_height
            offset = (
                styles.offset.resolve(
                    _Size(content_width.__floor__(), content_height.__floor__()),
                    viewport,
                )
                if styles.has_rule("offset")
                else NULL_OFFSET
            )

            placement = _WidgetPlacement(
                _Region(
                    box_margin.left,
                    y.__floor__(),
                    content_width.__floor__(),
                    next_y.__floor__() - y.__floor__(),
                ),
                offset,
                box_margin,
                widget,
                0,
                False,
                overlay,
            )
            if has_rule("constrain_x") or has_rule("constrain_y"):
                placement = placement.apply_constrain(
                    viewport.region if placement.overlay else size.region
                )
            add_placement(placement)
            if not overlay:
                y = next_y + margin

        return placements
