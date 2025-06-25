import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { motion } from "framer-motion"
import { cn } from "../utils/cn"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        gradient:
          "bg-gradient-to-r from-elf-500 to-purple-500 text-white hover:from-elf-600 hover:to-purple-600",
        glow: "bg-primary text-primary-foreground relative overflow-hidden",
        glass: "glass hover:bg-white/20 dark:hover:bg-white/10",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
      animation: {
        none: "",
        pulse: "animate-pulse",
        bounce: "hover:animate-bounce",
        wiggle: "hover:animate-wiggle",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      animation: "none",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: "left" | "right"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant,
    size,
    animation,
    asChild = false,
    loading = false,
    icon,
    iconPosition = "left",
    children,
    disabled,
    ...props
  }, ref) => {

    const buttonContent = (
      <>
        {loading && (
          <motion.div
            className="mr-2"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </motion.div>
        )}
        {icon && iconPosition === "left" && !loading && (
          <span className="mr-2">{icon}</span>
        )}
        {children}
        {icon && iconPosition === "right" && !loading && (
          <span className="ml-2">{icon}</span>
        )}
      </>
    )

    if (asChild) {
      return (
        <Slot
          className={cn(buttonVariants({ variant, size, animation, className }))}
          ref={ref}
          {...props}
        >
          {variant === "glow" ? (
            <>
              <span className="relative z-10">{buttonContent}</span>
              <div className="absolute inset-0 bg-gradient-to-r from-elf-400 to-purple-400 opacity-0 hover:opacity-30 transition-opacity duration-300" />
            </>
          ) : (
            buttonContent
          )}
        </Slot>
      )
    }

    return (
      <motion.button
        className={cn(buttonVariants({ variant, size, animation, className }))}
        ref={ref}
        disabled={disabled || loading}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        {...props}
      >
        {variant === "glow" ? (
          <>
            <span className="relative z-10">{buttonContent}</span>
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-elf-400 to-purple-400 opacity-0"
              whileHover={{ opacity: 0.3 }}
              transition={{ duration: 0.3 }}
            />
          </>
        ) : (
          buttonContent
        )}
      </motion.button>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
