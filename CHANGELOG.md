# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0.dev0] - In Development

### Planned
- Implementation of historical chart data (older charts)
- Additional year exploration features

## [0.1.1] - 2025-10-25

### Added
- Feedback submission system with webhook integration
- Email notifications for user feedback (via Zapier webhook)
- Fallback to local SMTP for development environment
- Feedback logging to `feedback_log.txt` for reliability
- Environment variable support via `.env` file

### Changed
- Centered app layout for larger screens
- Improved mobile responsiveness with CSS media queries (768px and 480px breakpoints)
- Better error handling and user feedback messages

### Fixed
- Layout shifting to left on desktop screens
- Mobile display issues with responsive design

## [0.1.0] - Initial Release

### Added
- Initial Gradio dashboard for music chart exploration
- Integration with Google Sheets data source
- Interactive visualizations with Plotly
- Basic song and chart browsing functionality
