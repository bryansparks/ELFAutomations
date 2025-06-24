# ELF UI/UX Design System

## Overview

The ELF UI Design System is a comprehensive framework for building professional, animated, and distinctive user interfaces for the ELF Automations ecosystem. It dramatically reduces frontend development time while ensuring consistency and quality across all applications.

## Key Features

### 🎨 Professional Design
- **Motion-First**: Every interaction includes purposeful animations
- **Multiple Themes**: Ocean, Sunset, Forest, Neon, and custom themes
- **Glass Morphism & Neumorphism**: Modern UI effects
- **Gradient Utilities**: Dynamic gradients and mesh backgrounds
- **Custom Animations**: Page transitions, micro-interactions, loading states

### ⚡ Rapid Development
- **CLI Tool**: `elf-ui create`, `elf-ui generate`, `elf-ui connect`
- **Smart Templates**: Dashboard, Admin, Workflow, Analytics, Communication
- **Component Generation**: Auto-generate CRUD operations with animations
- **API Integration**: Connect to OpenAPI/GraphQL and generate types/hooks
- **Hot Module Replacement Plus**: Instant preview with state preservation

### 🧩 Component Library
- **Enhanced shadcn/ui**: Extended with animations and variants
- **Specialized Components**: MetricCard, TeamHierarchy, CostTrends
- **Loading States**: 5 animated variants (dots, pulse, wave, orbit, morph)
- **Page Transitions**: Fade, slide, scale, rotate, morph effects
- **Motion Components**: Powered by Framer Motion

### 🏗️ Architecture
- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript with strict mode
- **Styling**: Tailwind CSS + CSS-in-JS for animations
- **State Management**: Zustand (local) + React Query (server)
- **Real-time**: WebSocket support with Socket.io
- **Charts**: Recharts + D3 for custom visualizations

## Getting Started

### Installation

```bash
# Install the UI package in your project
npm install @elf/ui

# Install the CLI globally
npm install -g @elf/cli
```

### Create a New Project

```bash
# Create a new ELF application
elf-ui create my-app --template=dashboard

# Navigate to the project
cd my-app

# Start development server
npm run dev
```

### Use in Existing Project

1. Add to your `tailwind.config.js`:
```js
module.exports = {
  presets: [require('@elf/ui/tailwind.config')],
  content: [
    // ... your content paths
    './node_modules/@elf/ui/dist/**/*.{js,ts,jsx,tsx}'
  ],
}
```

2. Import the theme CSS:
```tsx
// In your root layout or _app.tsx
import '@elf/ui/themes/index.css'
```

3. Start using components:
```tsx
import { Button, Card, MetricCard, PageTransition } from '@elf/ui'

export default function MyPage() {
  return (
    <PageTransition variant="fade">
      <Card variant="glass" hover="lift">
        <MetricCard
          title="Total Users"
          value={1234}
          change={12.5}
          animate
        />
        <Button variant="gradient">Get Started</Button>
      </Card>
    </PageTransition>
  )
}
```

## Component Examples

### Animated Button
```tsx
<Button
  variant="glow"
  size="lg"
  icon={<Zap />}
  loading={isLoading}
>
  Execute Action
</Button>
```

### Metric Card with Animation
```tsx
<MetricCard
  title="Revenue"
  value={45231}
  prefix="$"
  change={20.1}
  changeLabel="from last month"
  icon={<DollarSign className="h-4 w-4" />}
  color="success"
  animate
/>
```

### Page Transition
```tsx
<PageTransition variant="slide" direction="up" duration={0.5}>
  <YourContent />
</PageTransition>
```

### Loading States
```tsx
// Different loading animations
<Loading variant="dots" />
<Loading variant="pulse" size="lg" />
<Loading variant="wave" color="gradient" />
<Loading variant="orbit" />
<Loading variant="morph" />
```

## CLI Commands

### Create New App
```bash
elf-ui create <name> [options]
  --template    Template to use (dashboard|admin|workflow|analytics|communication)
  --auth        Add authentication provider
  --no-install  Skip dependency installation
```

### Generate Components
```bash
elf-ui generate <type> <name> [options]
  type: component|page|hook
  --crud        Add CRUD operations
  --animate     Add animations
  --api         Include API integration
```

### Connect to API
```bash
elf-ui connect api [options]
  --swagger <path>    OpenAPI/Swagger spec path
  --graphql <url>     GraphQL endpoint
  --generate-hooks    Generate React hooks
  --generate-types    Generate TypeScript types
```

## Templates

### 1. Dashboard Template
- Real-time metrics and charts
- WebSocket integration
- Cost analytics
- System monitoring

### 2. Admin Panel Template
- CRUD operations
- User management
- Data tables with filtering
- Form validation

### 3. Workflow Builder Template
- Drag-and-drop interface
- Visual programming
- State management
- Node-based editor

### 4. Analytics Template
- Advanced charting
- Data exploration
- Report generation
- Export functionality

### 5. Communication Hub Template
- Real-time messaging
- Notification system
- Activity feeds
- Team collaboration

## Theming

### Built-in Themes
```tsx
// Apply theme classes to html element
<html className="dark theme-ocean">
```

Available themes:
- Default (ELF blue)
- Ocean (Deep blues)
- Sunset (Warm oranges/pinks)
- Forest (Natural greens)
- Neon (Vibrant purples)

### Custom Theme
```css
.theme-custom {
  --primary: 142 76% 36%;
  --gradient-start: 142 76% 36%;
  --gradient-middle: 162 63% 41%;
  --gradient-end: 88 50% 53%;
}
```

## Performance

- **Bundle Size**: Tree-shaking enabled
- **Code Splitting**: Automatic with Next.js
- **Lazy Loading**: Components loaded on demand
- **Optimized Animations**: GPU-accelerated transforms
- **Image Optimization**: Next.js Image component

## Best Practices

1. **Use Semantic Variants**: Choose button/card variants that match their purpose
2. **Consistent Animation**: Use the same transition types within a flow
3. **Loading States**: Always show loading feedback for async operations
4. **Accessibility**: All components follow WCAG 2.1 AA guidelines
5. **Mobile First**: Design for mobile, enhance for desktop

## ELF Control Center

The flagship implementation using this design system is the ELF Control Center, which provides:

- **System Overview**: Real-time stats and health monitoring
- **Team Management**: Visual hierarchy and team creation
- **Workflow Control**: N8N integration and execution
- **Cost Analytics**: Budget tracking and optimization
- **Communication Hub**: A2A message visualization
- **Security Center**: Credential and access management

## Future Enhancements

- **Visual Builder**: Drag-drop UI builder
- **Design Tokens**: Figma integration
- **Component AI**: Generate components from descriptions
- **Performance Monitoring**: Built-in analytics
- **Collaboration Tools**: Real-time design collaboration

## Contributing

The ELF UI Design System is designed to evolve with the needs of the ELF ecosystem. To add new components or enhance existing ones:

1. Components go in `packages/ui/src/components/`
2. Follow the established patterns
3. Include Storybook stories
4. Add comprehensive TypeScript types
5. Document with examples

## Support

For issues, feature requests, or contributions:
- GitHub: [ELFAutomations/ui](https://github.com/ELFAutomations/ui)
- Documentation: [docs.elf.ai/ui](https://docs.elf.ai/ui)
- Discord: [ELF Community](https://discord.gg/elf)
