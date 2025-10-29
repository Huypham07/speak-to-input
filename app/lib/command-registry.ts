export interface CommandField {
  name: string
  type: "string" | "number" | "date" | "select"
  required: boolean
  options?: string[]
}

export interface Command {
  id: string
  name: string
  description: string
  fields: CommandField[]
  pattern: RegExp
  extract: (text: string) => Record<string, any> | null
}

// Command registry for mapping speech to actions
export const commandRegistry: Record<string, Command> = {
  transfer: {
    id: "transfer",
    name: "Transfer Money",
    description: "Send money to another account",
    fields: [
      { name: "recipientName", type: "string", required: true },
      { name: "recipientAccount", type: "string", required: true },
      { name: "amount", type: "number", required: true },
      { name: "description", type: "string", required: false },
    ],
    pattern: /transfer|send|pay/i,
    extract: (text: string) => {
      const amountMatch = text.match(/(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)/i)
      const nameMatch = text.match(/(?:to|for)\s+([a-z\s]+?)(?:\s+account|\s+number|\s+$)/i)
      const accountMatch = text.match(/account\s*(?:number)?\s*(\d+)/i)

      if (amountMatch && nameMatch && accountMatch) {
        return {
          amount: Number.parseFloat(amountMatch[1]),
          recipientName: nameMatch[1].trim(),
          recipientAccount: accountMatch[1],
          description: "",
        }
      }
      return null
    },
  },

  bill: {
    id: "bill",
    name: "Create Expense Bill",
    description: "Create a new expense bill",
    fields: [
      { name: "title", type: "string", required: true },
      {
        name: "category",
        type: "select",
        required: true,
        options: ["Utilities", "Rent", "Insurance", "Subscription", "Healthcare", "Education", "Other"],
      },
      { name: "amount", type: "number", required: true },
      { name: "dueDate", type: "date", required: true },
      { name: "description", type: "string", required: false },
    ],
    pattern: /bill|expense|payment/i,
    extract: (text: string) => {
      const amountMatch = text.match(/(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)/i)
      const titleMatch = text.match(/(?:bill|expense|payment)\s+(?:for\s+)?([a-z\s]+?)(?:\s+\d+|\s+$)/i)
      const categoryMatch = text.match(/(?:utilities|rent|insurance|subscription|healthcare|education)/i)

      if (amountMatch && titleMatch) {
        return {
          amount: Number.parseFloat(amountMatch[1]),
          title: titleMatch[1].trim(),
          category: categoryMatch ? categoryMatch[0].charAt(0).toUpperCase() + categoryMatch[0].slice(1) : "Other",
          dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
          description: "",
        }
      }
      return null
    },
  },

  fund: {
    id: "fund",
    name: "Create Savings Fund",
    description: "Create a new savings fund",
    fields: [
      { name: "name", type: "string", required: true },
      { name: "targetAmount", type: "number", required: true },
      {
        name: "category",
        type: "select",
        required: true,
        options: ["Vacation", "Emergency", "Education", "Home", "Car", "Wedding", "Other"],
      },
      { name: "deadline", type: "date", required: true },
      { name: "priority", type: "select", required: true, options: ["low", "medium", "high"] },
    ],
    pattern: /fund|savings|goal|save/i,
    extract: (text: string) => {
      const amountMatch = text.match(/(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)/i)
      const nameMatch = text.match(/(?:fund|savings|goal)\s+(?:for\s+)?([a-z\s]+?)(?:\s+\d+|\s+$)/i)
      const categoryMatch = text.match(/(?:vacation|emergency|education|home|car|wedding)/i)

      if (amountMatch && nameMatch) {
        return {
          targetAmount: Number.parseFloat(amountMatch[1]),
          currentAmount: 0,
          name: nameMatch[1].trim(),
          category: categoryMatch ? categoryMatch[0].charAt(0).toUpperCase() + categoryMatch[0].slice(1) : "Other",
          deadline: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
          priority: "medium",
          description: "",
        }
      }
      return null
    },
  },
}

export function matchCommand(text: string): { command: Command; data: Record<string, any> } | null {
  for (const command of Object.values(commandRegistry)) {
    if (command.pattern.test(text)) {
      const data = command.extract(text)
      if (data) {
        return { command, data }
      }
    }
  }
  return null
}
