





from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, Property, QPoint, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont, QPainterPath, QBrush, QPalette

class ChartBar(QFrame):
    """
    Custom animated bar for bar charts.
    """
    def __init__(self, value, max_value, color="#fb923c", parent=None):
        super().__init__(parent)
        
        self.value = value
        self.max_value = max(max_value, 1)  # Prevent division by zero
        self.display_value = 0  # For animation
        self.color = QColor(color)
        self.gradient_color = QColor(color)
        self.gradient_color.setAlpha(100)
        
        # Set fixed height for the bar
        self.setMinimumHeight(24)
        self.setMaximumHeight(24)
        
        # Set frame style
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            background-color: transparent;
            border-radius: 4px;
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Prepare animation
        self.animation = QPropertyAnimation(self, b"displayValue")
        self.animation.setDuration(800)
        self.animation.setStartValue(0)
        self.animation.setEndValue(value)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Connect animation to update
        self.animation.valueChanged.connect(self.update)
    
    def get_display_value(self):
        return self.display_value
    
    def set_display_value(self, value):
        self.display_value = value
        self.update()
    
    displayValue = Property(float, get_display_value, set_display_value)
    
    def paintEvent(self, event):
        """Paint the bar with gradient and rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate width percentage
        width = self.width() * (self.display_value / self.max_value)
        
        if width > 0:
            # Create rounded rect path
            path = QPainterPath()
            path.addRoundedRect(0, 0, width, self.height(), 4, 4)
            
            # Create gradient
            gradient = QLinearGradient(0, 0, width, 0)
            gradient.setColorAt(0, self.color)
            gradient.setColorAt(1, self.gradient_color)
            
            # Fill with gradient
            painter.fillPath(path, QBrush(gradient))
    
    def start_animation(self):
        """Start the bar animation."""
        self.animation.start()


class BarChartWidget(QWidget):
    """
    Custom animated bar chart widget.
    """
    def __init__(self, data, title="", color="#fb923c", parent=None):
        super().__init__(parent)
        
        self.data = data
        self.color = color
        self.bars = []
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Add title if provided
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            """)
            layout.addWidget(title_label)
        
        # Add chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            background-color: rgba(26, 26, 26, 0.7);
            border-radius: 8px;
            padding: 15px;
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setSpacing(12)
        
        # Find max value for scaling
        max_value = max(data.values()) if data else 1
        
        # Create bars for each item
        for key, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            item_layout = QHBoxLayout()
            
            # Label
            label = QLabel(key)
            label.setStyleSheet("color: #d1cccc;")
            label.setMinimumWidth(120)
            
            # Bar
            bar = ChartBar(value, max_value, color)
            self.bars.append(bar)
            
            # Value label
            value_label = QLabel(str(value))
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setStyleSheet("color: #d1cccc;")
            value_label.setMinimumWidth(50)
            
            item_layout.addWidget(label)
            item_layout.addWidget(bar, 1)  # Give stretch to the bar
            item_layout.addWidget(value_label)
            
            chart_layout.addLayout(item_layout)
        
        layout.addWidget(chart_frame)
    
    def showEvent(self, event):
        """Start animations when widget becomes visible."""
        super().showEvent(event)
        
        # Start animations with slight delay between bars
        for i, bar in enumerate(self.bars):
            QTimer.singleShot(i * 50, bar.start_animation)


class DonutChartWidget(QWidget):
    """
    Custom donut chart widget for showing distributions.
    """
    def __init__(self, data, title="", parent=None):
        super().__init__(parent)
        
        self.data = data
        self.title = title
        
        # Assign colors to categories
        self.colors = [
            "#fb923c",  # Orange
            "#3b82f6",  # Blue
            "#10b981",  # Green
            "#a855f7",  # Purple
            "#f43f5e",  # Red
            "#0ea5e9",  # Sky blue
            "#f59e0b",  # Amber
            "#8b5cf6",  # Violet
            "#14b8a6",  # Teal
            "#ec4899"   # Pink
        ]
        
        # Calculate percentages
        total = sum(data.values())
        self.percentages = {k: (v / total) * 100 for k, v in data.items()}
        
        # Set minimum size
        self.setMinimumSize(300, 300)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add title if provided
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            """)
            layout.addWidget(title_label)
        
        # Empty placeholder for the actual chart (will be drawn in paintEvent)
        chart_widget = QWidget()
        chart_widget.setMinimumSize(200, 200)
        chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(chart_widget, 1)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_widget = QWidget()
        legend_widget.setLayout(legend_layout)
        
        # Create two columns for the legend
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()
        
        sorted_items = sorted(self.percentages.items(), key=lambda x: x[1], reverse=True)
        for i, (key, percentage) in enumerate(sorted_items):
            color = self.colors[i % len(self.colors)]
            
            legend_item = QHBoxLayout()
            
            # Color box
            color_box = QFrame()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"""
                background-color: {color};
                border-radius: 3px;
            """)
            
            # Label with percentage
            label = QLabel(f"{key} ({percentage:.1f}%)")
            label.setStyleSheet("color: #d1cccc;")
            
            legend_item.addWidget(color_box)
            legend_item.addWidget(label, 1)
            
            # Add to appropriate column (alternating)
            if i < len(sorted_items) / 2:
                left_column.addLayout(legend_item)
            else:
                right_column.addLayout(legend_item)
        
        legend_layout.addLayout(left_column)
        legend_layout.addLayout(right_column)
        layout.addWidget(legend_widget)
    
    def paintEvent(self, event):
        """Paint the donut chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define chart dimensions
        rect = self.rect()
        chart_rect = rect.adjusted(50, 50, -50, -90)  # Make room for title and legend
        center = chart_rect.center()
        
        # Calculate radius and donut thickness
        radius = min(chart_rect.width(), chart_rect.height()) / 2
        inner_radius = radius * 0.6  # Donut hole size
        
        # Draw the chart segments
        start_angle = 0
        sorted_items = sorted(self.percentages.items(), key=lambda x: x[1], reverse=True)
        
        for i, (key, percentage) in enumerate(sorted_items):
            span_angle = percentage * 3.6  # Convert percentage to degrees (360 / 100 = 3.6)
            color = self.colors[i % len(self.colors)]
            
            # Create path for the donut segment
            path = QPainterPath()
            path.moveTo(center)
            
            # Add the arc
            path.arcTo(
                chart_rect.adjusted(-radius, -radius, radius, radius),
                start_angle,
                span_angle
            )
            
            # Fill segment with color
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            painter.drawPath(path)
            
            # Move to next segment
            start_angle += span_angle
        
        # Draw the inner circle (donut hole)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2b2929"))  # Background color
        painter.drawEllipse(center, inner_radius, inner_radius)
        
        # Draw center text (total count)
        total = sum(self.data.values())
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRect(center.x() - inner_radius, center.y() - 20, inner_radius * 2, 40),
            Qt.AlignCenter,
            f"Total\n{total}"
        )


