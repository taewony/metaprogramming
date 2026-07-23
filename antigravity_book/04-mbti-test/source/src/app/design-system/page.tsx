import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"

export default function DesignSystemPage() {
  return (
    <div className="container mx-auto py-10 space-y-10">
      <div>
        <h1 className="text-3xl font-bold mb-4">Design System - Midnight Dev Studio</h1>
        <p className="text-muted-foreground">Component verification page.</p>
      </div>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">1. Buttons</h2>
        <div className="flex flex-wrap gap-4">
          <Button>Primary Button</Button>
          <Button variant="secondary">Secondary Button</Button>
          <Button variant="destructive">Destructive Button</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button variant="link">Link Button</Button>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">2. Cards (Glassmorphism)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="w-[350px]">
            <CardHeader>
              <CardTitle>Card Title</CardTitle>
              <CardDescription>Card Description goes here.</CardDescription>
            </CardHeader>
            <CardContent>
              <p>This is the content of the card using the glassmorphism style.</p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline">Cancel</Button>
              <Button>Submit</Button>
            </CardFooter>
          </Card>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">3. Progress Bar (Neon Glow)</h2>
        <div className="w-[60%] space-y-4">
          <Progress value={33} />
          <Progress value={66} />
          <Progress value={100} />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">4. Radio Group (Card Selection)</h2>
        <RadioGroup defaultValue="option-1" className="grid grid-cols-1 md:grid-cols-2 gap-4">
           <div>
            <RadioGroupItem value="option-1" id="option-1" className="peer sr-only" />
            <Label
              htmlFor="option-1"
              className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:text-primary"
            >
              <span className="text-lg font-semibold">Option A</span>
              <span className="text-sm text-muted-foreground">Description for Option A</span>
            </Label>
          </div>
          <div>
            <RadioGroupItem value="option-2" id="option-2" className="peer sr-only" />
            <Label
              htmlFor="option-2"
              className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:text-primary"
            >
              <span className="text-lg font-semibold">Option B</span>
              <span className="text-sm text-muted-foreground">Description for Option B</span>
            </Label>
          </div>
        </RadioGroup>
      </section>
    </div>
  )
}
