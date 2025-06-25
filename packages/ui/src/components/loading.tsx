import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "../utils/cn"

interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "dots" | "pulse" | "wave" | "orbit" | "morph"
  size?: "sm" | "md" | "lg"
  color?: "primary" | "secondary" | "gradient"
}

const sizeClasses = {
  sm: "h-8 w-8",
  md: "h-12 w-12",
  lg: "h-16 w-16"
}

const colorClasses = {
  primary: "bg-primary",
  secondary: "bg-secondary",
  gradient: "bg-gradient-to-r from-elf-500 to-purple-500"
}

const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(
  ({ className, variant = "dots", size = "md", color = "primary", ...props }, ref) => {
    const renderVariant = () => {
      switch (variant) {
        case "dots":
          return (
            <div className="flex space-x-2">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className={cn("h-3 w-3 rounded-full", colorClasses[color])}
                  animate={{
                    scale: [1, 1.5, 1],
                    opacity: [1, 0.5, 1],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.2,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
          )

        case "pulse":
          return (
            <motion.div
              className={cn(sizeClasses[size], "rounded-full", colorClasses[color])}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0.3, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          )

        case "wave":
          return (
            <div className="flex space-x-1">
              {[0, 1, 2, 3, 4].map((i) => (
                <motion.div
                  key={i}
                  className={cn("w-1 bg-primary rounded-full")}
                  animate={{
                    height: ["12px", "24px", "12px"],
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    delay: i * 0.15,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
          )

        case "orbit":
          return (
            <div className={cn(sizeClasses[size], "relative")}>
              <motion.div
                className={cn("absolute inset-0 rounded-full border-2",
                  color === "gradient" ? "border-elf-500" : "border-primary"
                )}
                style={{ borderTopColor: "transparent" }}
                animate={{ rotate: 360 }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: "linear"
                }}
              />
              <motion.div
                className={cn("absolute inset-2 rounded-full border-2",
                  color === "gradient" ? "border-purple-500" : "border-primary/50"
                )}
                style={{ borderBottomColor: "transparent" }}
                animate={{ rotate: -360 }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "linear"
                }}
              />
            </div>
          )

        case "morph":
          return (
            <motion.div
              className={cn(sizeClasses[size], colorClasses[color])}
              animate={{
                borderRadius: ["50%", "20%", "50%", "20%", "50%"],
                rotate: [0, 180, 360],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          )

        default:
          return null
      }
    }

    return (
      <div
        ref={ref}
        className={cn("flex items-center justify-center", className)}
        {...props}
      >
        {renderVariant()}
      </div>
    )
  }
)
Loading.displayName = "Loading"

// Skeleton loader with shimmer effect
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circle" | "rect"
  width?: string | number
  height?: string | number
  animate?: boolean
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant = "rect", width, height, animate = true, ...props }, ref) => {
    const variantClasses = {
      text: "h-4 w-full rounded",
      circle: "rounded-full",
      rect: "rounded-md"
    }

    return (
      <div
        ref={ref}
        className={cn(
          "bg-muted relative overflow-hidden",
          variantClasses[variant],
          animate && "shimmer",
          className
        )}
        style={{
          width: width || (variant === "circle" ? "40px" : "100%"),
          height: height || (variant === "circle" ? "40px" : variant === "text" ? "16px" : "60px")
        }}
        {...props}
      />
    )
  }
)
Skeleton.displayName = "Skeleton"

export { Loading, Skeleton }
