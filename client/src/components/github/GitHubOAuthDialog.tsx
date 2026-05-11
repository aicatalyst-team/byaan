import { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog'
import { Input } from '../ui/input'
import { Loader2, ExternalLink, Check, Github, KeyRound, Lock } from 'lucide-react'
import { openExternalUrl, isTauriApp } from '../../lib/tauri-api'
import { GitHubService } from '../../services/github'

interface GitHubOAuthDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
  oauthAvailable: boolean
}

type OAuthStep = 'idle' | 'redirecting' | 'waiting' | 'success' | 'error'

export function GitHubOAuthDialog({ open, onOpenChange, onSuccess, oauthAvailable }: GitHubOAuthDialogProps) {
  const [step, setStep] = useState<OAuthStep>('idle')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [oauthState, setOauthState] = useState('')
  const [authMethod, setAuthMethod] = useState<'oauth' | 'pat'>(oauthAvailable ? 'oauth' : 'pat')
  const [patToken, setPatToken] = useState('')
  const [patLoading, setPatLoading] = useState(false)

  useEffect(() => {
    setAuthMethod(oauthAvailable ? 'oauth' : 'pat')
  }, [oauthAvailable])

  const resetDialog = () => {
    setStep('idle')
    setError('')
    setOauthState('')
    setPatToken('')
    setAuthMethod(oauthAvailable ? 'oauth' : 'pat')
  }

  const handleClose = (newOpen: boolean) => {
    if (!newOpen) resetDialog()
    onOpenChange(newOpen)
  }

  useEffect(() => {
    if (!open || step !== 'waiting') return
    if (!isTauriApp()) return

    let cleanup: (() => void) | undefined

    const setupListener = async () => {
      const { listen } = await import('@tauri-apps/api/event')
      const unlisten = await listen<string>('deep-link-received', async (event) => {
        const url = event.payload
        if (!url.includes('github/callback')) return
        const params = new URLSearchParams(url.split('?')[1] || '')
        const code = params.get('code')
        if (!code) {
          setError('No authorization code received')
          setStep('error')
          return
        }
        try {
          await GitHubService.callbackOAuth(code, oauthState)
          setStep('success')
          onSuccess?.()
        } catch (err) {
          setError(err instanceof Error ? err.message : 'OAuth callback failed')
          setStep('error')
        }
      })
      cleanup = unlisten
    }

    setupListener()
    return () => { cleanup?.() }
  }, [open, step, oauthState, onSuccess])

  useEffect(() => {
    if (!open || step !== 'waiting') return

    if (isTauriApp()) {
      const checkInitialDeepLink = async () => {
        try {
          const { invoke } = await import('@tauri-apps/api/core')
          const url = await invoke<string | null>('get_initial_deep_link')
          if (url && url.includes('github/callback')) {
            const params = new URLSearchParams(url.split('?')[1] || '')
            const code = params.get('code')
            if (code) {
              await GitHubService.callbackOAuth(code, oauthState)
              setStep('success')
              onSuccess?.()
            }
          }
        } catch {}
      }
      checkInitialDeepLink()
      return
    }

    const interval = setInterval(async () => {
      try {
        const status = await GitHubService.getStatus()
        if (status.connected) {
          clearInterval(interval)
          setStep('success')
          onSuccess?.()
        }
      } catch {}
    }, 2000)

    return () => clearInterval(interval)
  }, [open, step, oauthState, onSuccess])

  const startOAuth = async () => {
    setLoading(true)
    setError('')
    try {
      const { auth_url, state } = await GitHubService.startOAuth()
      setOauthState(state)

      if (isTauriApp()) {
        await openExternalUrl(auth_url)
      } else {
        window.open(auth_url, '_blank', 'noopener,noreferrer')
      }
      setStep('waiting')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start OAuth')
      setStep('error')
    } finally {
      setLoading(false)
    }
  }

  const connectWithPAT = async () => {
    setPatLoading(true)
    setError('')
    try {
      await GitHubService.connectWithPAT(patToken)
      setStep('success')
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect with PAT')
      setStep('error')
    } finally {
      setPatLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg bg-[#2a2a2a] border-[#444444]">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Github className="w-5 h-5" />
            {step === 'success' ? 'GitHub Connected' : 'Connect GitHub'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {step === 'idle' && (
            <>
              <p className="text-sm text-gray-400">
                Connect your GitHub account to analyze repositories and build codebase skills.
              </p>

              {oauthAvailable && (
                <div className="flex gap-1 bg-[#1a1a1a] rounded-lg p-1">
                  <button
                    onClick={() => setAuthMethod('oauth')}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                      authMethod === 'oauth'
                        ? 'bg-[#3a3a3a] text-white'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    <Github className="w-4 h-4" />
                    OAuth
                  </button>
                  <button
                    onClick={() => setAuthMethod('pat')}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                      authMethod === 'pat'
                        ? 'bg-[#3a3a3a] text-white'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    <KeyRound className="w-4 h-4" />
                    Access Token
                  </button>
                </div>
              )}

              {authMethod === 'oauth' && oauthAvailable ? (
                <>
                  <div className="bg-[#1a1a1a] border border-gray-800 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 mb-2">
                      <Lock className="w-3 h-3 text-gray-500" />
                      <span className="text-xs text-gray-500">Permissions requested:</span>
                    </div>
                    <ul className="text-xs text-gray-500 space-y-1 ml-[18px]">
                      <li><span className="text-gray-400 font-mono">repo</span> — Full access to public and private repositories <span className="text-gray-600">(required)</span></li>
                      <li><span className="text-gray-400 font-mono">read:user</span> — Read your GitHub profile info <span className="text-gray-600">(optional)</span></li>
                    </ul>
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <Button variant="outline" onClick={() => handleClose(false)} className="border-[#555555] text-white hover:bg-[#3a3a3a]">
                      Cancel
                    </Button>
                    <Button onClick={startOAuth} disabled={loading} className="bg-brand-orange hover:bg-brand-orange/90 flex items-center gap-2">
                      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                      <ExternalLink className="w-4 h-4" />
                      Authorize with GitHub
                    </Button>
                  </div>
                </>
              ) : (
                <div className="space-y-3">
                  <Input
                    type="password"
                    value={patToken}
                    onChange={(e) => setPatToken(e.target.value)}
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                    className="bg-[#1a1a1a] border-gray-700 text-white font-mono text-sm"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && patToken.trim()) connectWithPAT()
                    }}
                  />
                  <p className="text-xs text-gray-500">
                    Create a token at{' '}
                    <a
                      href="https://github.com/settings/tokens"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand-orange hover:underline"
                    >
                      github.com/settings/tokens
                    </a>
                    {' '}with these scopes:
                  </p>
                  <ul className="text-xs text-gray-500 space-y-1 mt-1 ml-3">
                    <li><span className="text-gray-400 font-mono">repo</span> — Full access to public and private repositories <span className="text-gray-600">(required)</span></li>
                    <li><span className="text-gray-400 font-mono">read:user</span> — Read your GitHub profile info <span className="text-gray-600">(optional)</span></li>
                  </ul>
                  <div className="flex justify-end gap-2 pt-1">
                    <Button variant="outline" onClick={() => handleClose(false)} className="border-[#555555] text-white hover:bg-[#3a3a3a]">
                      Cancel
                    </Button>
                    <Button
                      onClick={connectWithPAT}
                      disabled={patLoading || !patToken.trim()}
                      className="bg-brand-orange hover:bg-brand-orange/90 flex items-center gap-2"
                    >
                      {patLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                      Connect
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}

          {step === 'redirecting' && (
            <div className="text-center py-4">
              <Loader2 className="w-8 h-8 animate-spin text-brand-orange mx-auto mb-3" />
              <p className="text-sm text-gray-400">Opening GitHub authorization...</p>
            </div>
          )}

          {step === 'waiting' && (
            <div className="text-center py-4">
              <Loader2 className="w-8 h-8 animate-spin text-brand-orange mx-auto mb-3" />
              <p className="text-sm text-gray-400">Waiting for GitHub authorization...</p>
              <p className="text-xs text-gray-500 mt-2">Complete the authorization in your browser, then return here.</p>
            </div>
          )}

          {step === 'success' && (
            <>
              <div className="p-4 bg-green-900/20 border border-green-500 rounded-md text-center">
                <Check className="w-12 h-12 text-green-400 mx-auto mb-3" />
                <p className="text-green-400 font-medium mb-2">GitHub connected successfully!</p>
                <p className="text-sm text-gray-400">You can now connect and analyze repositories.</p>
              </div>
              <div className="flex justify-end pt-2">
                <Button onClick={() => handleClose(false)} className="bg-brand-orange hover:bg-brand-orange/90">Done</Button>
              </div>
            </>
          )}

          {step === 'error' && (
            <>
              <div className="p-4 bg-red-900/20 border border-red-500 rounded-md text-center">
                <p className="text-red-400 font-medium mb-2">Connection Failed</p>
                <p className="text-sm text-gray-400">{error || 'An error occurred.'}</p>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => handleClose(false)} className="border-[#555555] text-white hover:bg-[#3a3a3a]">Cancel</Button>
                <Button onClick={() => { resetDialog() }} className="bg-brand-orange hover:bg-brand-orange/90">Try Again</Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
