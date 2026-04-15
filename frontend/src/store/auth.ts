import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserInfo, LoginResponse } from '@/types'

interface AuthState {
  token: string | null
  user: UserInfo | null
  isAuthenticated: boolean
  setAuth: (data: LoginResponse) => void
  logout: () => void
  updateUser: (user: UserInfo) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      
      setAuth: (data: LoginResponse) => {
        set({
          token: data.access_token,
          user: data.user,
          isAuthenticated: true,
        })
      },
      
      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        })
      },
      
      updateUser: (user: UserInfo) => {
        set({ user })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
