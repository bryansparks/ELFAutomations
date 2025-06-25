import * as React from "react"
import { motion, type HTMLMotionProps } from "framer-motion"
import { cn } from "../utils/cn"

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glass" | "gradient" | "glow" | "neu"
  hover?: "none" | "lift" | "glow" | "rotate"
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", hover = "none", ...props }, ref) => {
    const variantClasses = {
      default: "rounded-lg border bg-card text-card-foreground shadow-sm",
      glass: "rounded-lg glass text-card-foreground",
      gradient: "rounded-lg bg-gradient-to-br from-elf-500/10 to-purple-500/10 border border-elf-500/20",
      glow: "rounded-lg bg-card text-card-foreground shadow-sm glow",
      neu: "rounded-lg neu text-card-foreground",
    }

    const hoverVariants = {
      none: {},
      lift: {
        whileHover: { y: -4, transition: { type: "spring", stiffness: 300 } }
      },
      glow: {
        whileHover: {
          boxShadow: "0 0 30px rgba(14, 165, 233, 0.3)",
          transition: { duration: 0.3 }
        }
      },
      rotate: {
        whileHover: {
          rotate: 1,
          transition: { type: "spring", stiffness: 300 }
        }
      }
    }

    return (
      <motion.div
        ref={ref}
        className={cn(variantClasses[variant], className)}
        {...hoverVariants[hover]}
        {...props}
      />
    )
  }
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
