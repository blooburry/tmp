from datetime import datetime
from typing import Any

from pandas import DataFrame, Series, concat
from panel import bind, depends
from panel.pane import HTML, ECharts
from panel.viewable import Viewable
from panel.widgets import Button, DatetimePicker, IntInput, Tabulator
from param import Date, Integer, Parameterized, String
from param import DataFrame as DF
from param.parameterized import Event


class OrangeProductionWidget(Parameterized):
    """
    Widget managing orange production records and visualisations.
    """

    # List of records:
    # [{"timestamp": datetime, "amount": int}, ...]
    records: DataFrame = DF(DataFrame(  # pyright: ignore[reportAssignmentType]
        {
            "timestamp": Series(dtype="datetime64[ns]"),
            "amount": Series(dtype=int)
        }
    ))

    # Form fields
    new_timestamp: datetime = Date(  # pyright: ignore[reportAssignmentType]
        default=None,
        doc="Timestamp of the production record.",
    )

    new_amount: int = Integer(  # pyright: ignore[reportAssignmentType]
        default=None,  # pyright: ignore[reportArgumentType]
        doc="Number of oranges produced.",
    )

    # User feedback info
    feedback: str = String(default="")  # pyright: ignore[reportAssignmentType]

    def __init__(self) -> None:
        super().__init__()

        # ---- form widgets (exposed as roots)
        self.timestamp_input = DatetimePicker.from_param(  # pyright: ignore[reportUnknownMemberType]
            self.param.new_timestamp,
            name="",
            width=250,
        )

        self.amount_input = IntInput.from_param(  # pyright: ignore[reportUnknownMemberType]
            self.param.new_amount,
            name="",
            width=200,
        )

        self.add_button = Button(name="Add record", button_type="primary")  # pyright: ignore[reportUnknownMemberType]
        bind(self._add_record, self.add_button, watch=True)

        # ---- visual components
        self._chart = ECharts(self._empty_chart_option(), height=350, sizing_mode="stretch_width")
        self._table = Tabulator.from_param(  # pyright: ignore[reportUnknownMemberType]
            self.param.records,
            show_index=False,
            sizing_mode="stretch_width",
            layout='fit_data_stretch',
            pagination="local",
            page_size=10,
            titles={
                "timestamp": "Timestamp",
                "amount": "Oranges produced",
            }
        )

        self._feedback_display = HTML(bind(str, self.param.feedback))  # pyright: ignore[reportUnknownArgumentType]

    def _add_record(self, _: Event) -> None:
        """
        Append a new record using the current form values.

        Validation is handled by Param:
        - new_amount must be an integer
        - must be >= 0
        - must not be empty
        - timestamp must not be empty
        """

        if self.timestamp_input.value is None:
            self.feedback = "Error: Please select a valid timestamp."
            self._feedback_display.css_classes = ["error"]
            return
        if self.amount_input.value is None or self.new_amount < 0:
            self.feedback = "Error: Please enter a valid number of oranges."
            self._feedback_display.css_classes = ["error"]
            return

        new_row = DataFrame({"timestamp": [self.new_timestamp], "amount": [self.new_amount]})
        
        self.records = concat([self.records, new_row], ignore_index=True) \
            .sort_values("timestamp") \
            .reset_index(drop=True)

        self.feedback = f"Record added: {self.new_amount} oranges at {self.new_timestamp:%Y-%m-%d %H:%M:%S}"
        self._feedback_display.css_classes = ["success"]

    @depends("records", watch=True)
    def _update_chart(self) -> None:
        option = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "time",
                "name": "Time",
            },
            "yAxis": {
                "type": "value",
                "name": "Total oranges",
            },
            "series": [
                {
                    "type": "line",
                    "name": "Total production",
                    "smooth": False,
                    "showSymbol": True,
                    "data": [
                        [ts.timestamp() * 1000, amount]
                        for ts, amount in zip(self.records["timestamp"], self.records["amount"])
                    ]
                }
            ],
        }

        self._chart.object = option

    def _empty_chart_option(self) -> dict[str, Any]:
        return {
            "xAxis": {"type": "time"},
            "yAxis": {"type": "value"},
            "series": [],
        }

    def roots(self) -> dict[str, Viewable]:
        return {
            "timestamp_input": self.timestamp_input,
            "amount_input": self.amount_input,
            "add_button": self.add_button,
            "production_chart": self._chart,
            "production_table": self._table,
            "feedback_box": self._feedback_display
        }