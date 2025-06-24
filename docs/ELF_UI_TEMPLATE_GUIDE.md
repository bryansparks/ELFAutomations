# ELF UI Template Guide

## Overview

The ELF UI Template is a comprehensive design system and application template extracted from the ElfAutomations.ai Control Center. It provides a complete foundation for building professional, modern web applications with a consistent look and feel.

## Quick Start

### Create a New App

```bash
./scripts/create-elf-app.sh my-awesome-app
cd packages/templates/my-awesome-app
npm install
npm run dev
```

## What's Included

### 1. Component Library (`@elf/ui`)

#### Buttons
```tsx
// Variants
<Button variant="default">Default</Button>
<Button variant="gradient">Gradient</Button>
<Button variant="outline">Outline</Button>
<Button variant="destructive">Delete</Button>
<Button variant="glow">Glow Effect</Button>
<Button variant="glass">Glass</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
```

#### Cards
```tsx
// Variants with hover effects
<Card variant="default" hover="none">Basic Card</Card>
<Card variant="glass" hover="lift">Glass with Lift</Card>
<Card variant="gradient" hover="glow">Gradient with Glow</Card>
<Card variant="neu" hover="lift">Neumorphic</Card>
```

#### MetricCard
```tsx
<MetricCard
  title="Revenue"
  value={125000}
  prefix="$"
  change={12.5}
  changeLabel="from last month"
  icon={<DollarSign />}
  color="success"
  animate
/>
```

#### Loading Animations
```tsx
<Loading variant="dots" />    // Three bouncing dots
<Loading variant="pulse" />   // Pulsing circle
<Loading variant="wave" />    // Wave animation
<Loading variant="orbit" />   // Orbiting dots
<Loading variant="morph" />   // Morphing shapes
```

#### Page Transitions
```tsx
<PageTransition variant="fade">
  {/* Page content */}
</PageTransition>

// Variants: fade, slide, scale
```

### 2. Design System

#### Color Palette
- **Primary**: ELF Blue (#0ea5e9)
- **Secondary**: Violet (#a855f7)
- **Accent**: Purple (#9333ea)
- **Success**: Green (#10b981)
- **Warning**: Yellow (#f59e0b)
- **Danger**: Red (#ef4444)

#### Gradients
```css
/* CSS classes */
.text-gradient     /* Blue to purple gradient text */
.gradient-elf      /* Background gradient */
.gradient-mesh-elf /* Mesh gradient background */
```

#### Effects
- **Glass Morphism**: `.glass` class
- **Neumorphism**: Built into Card variant
- **Glow Effects**: Button and Card hover states
- **Smooth Animations**: All transitions use cubic-bezier easing

### 3. Layout Patterns

#### Standard App Layout
```tsx
// Collapsible sidebar navigation
// Main content area with padding
// Responsive grid system
// Dark theme by default
```

#### Dashboard Grid
```tsx
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
  {/* Metric cards */}
</div>
```

#### Page Structure
```tsx
<PageTransition variant="fade">
  <div className="p-6 space-y-6">
    {/* Page header */}
    <div>
      <h1 className="text-3xl font-bold">Page Title</h1>
      <p className="text-muted-foreground mt-1">Description</p>
    </div>

    {/* Page content */}
    {/* ... */}
  </div>
</PageTransition>
```

### 4. Data Fetching Pattern

```tsx
// Custom hook pattern
export function useData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/data')
      const data = await response.json()
      setData(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, refetch: fetchData }
}
```

## Common Patterns

### 1. Dashboard Page
```tsx
export default function DashboardPage() {
  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gradient">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your application</p>
        </div>

        {/* Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard {...} />
        </div>

        {/* Content Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card variant="glass">...</Card>
          <Card variant="gradient">...</Card>
        </div>
      </div>
    </PageTransition>
  )
}
```

### 2. List/Table Page
```tsx
<Card variant="gradient">
  <CardHeader>
    <CardTitle>Items</CardTitle>
  </CardHeader>
  <CardContent>
    {loading ? (
      <Loading variant="dots" />
    ) : (
      <div className="space-y-4">
        {items.map(item => (
          <div key={item.id} className="flex items-center justify-between p-4 rounded-lg bg-background/50 hover:bg-accent">
            {/* Item content */}
          </div>
        ))}
      </div>
    )}
  </CardContent>
</Card>
```

### 3. Form Page
```tsx
<Card variant="neu">
  <CardHeader>
    <CardTitle>Settings</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium">Field Label</label>
        <input
          type="text"
          className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
        />
      </div>

      <label className="flex items-center justify-between">
        <span className="text-sm">Enable Feature</span>
        <input type="checkbox" className="toggle" />
      </label>
    </div>
  </CardContent>
</Card>
```

## Customization

### 1. Update Brand Colors
Edit `src/styles/globals.css`:
```css
:root {
  --primary: 199 89% 48%;        /* Change to your brand color */
  --gradient-start: 199 89% 48%; /* Update gradient colors */
  --gradient-end: 280 87% 65%;
}
```

### 2. Add New Navigation Items
Edit `src/components/navigation.tsx`:
```tsx
const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Your Page', href: '/your-page', icon: YourIcon },
  // Add more items
]
```

### 3. Create Custom Components
Add to `packages/ui/src/components/`:
```tsx
export function CustomComponent({ ...props }) {
  return (
    <div className="your-styles">
      {/* Component content */}
    </div>
  )
}
```

## Best Practices

1. **Consistent Spacing**: Use Tailwind's spacing scale (p-4, space-y-6, gap-4)
2. **Loading States**: Always show loading states for async operations
3. **Error Handling**: Provide clear error messages and retry options
4. **Animations**: Use PageTransition for route changes, keep animations subtle
5. **Responsive Design**: Test on mobile, use Tailwind's responsive prefixes
6. **Dark Theme**: Design for dark theme first, it's the default

## Examples of Apps You Can Build

1. **Admin Dashboard**: Analytics, user management, settings
2. **Project Management**: Tasks, teams, timelines
3. **CRM System**: Contacts, deals, communications
4. **Monitoring Dashboard**: Metrics, alerts, logs
5. **E-commerce Backend**: Products, orders, customers
6. **Content Management**: Posts, media, categories

## Tips for Success

1. **Start Small**: Use the basic template and add features incrementally
2. **Reuse Components**: The UI library has most of what you need
3. **Follow Patterns**: Stick to the established patterns for consistency
4. **Keep It Simple**: The template is powerful but don't overcomplicate
5. **Performance**: Use React Query for data fetching, lazy load heavy components

## Resources

- **Component Storybook**: Build a storybook to showcase components
- **Figma Template**: Export the design system to Figma
- **API Integration**: Use the fetch pattern or add React Query
- **State Management**: Zustand is included and configured
- **Testing**: Add Vitest and React Testing Library

## Next Steps

1. Create your app: `./scripts/create-elf-app.sh your-app`
2. Customize the navigation and home page
3. Build your features using the component library
4. Deploy with your preferred hosting service

The ELF UI Template gives you a massive head start on any web application, with professional design, smooth animations, and battle-tested patterns. Happy building! 🚀
