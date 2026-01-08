<x-filament-panels::page>
    {{-- Stats Cards --}}
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="fi-wi-stats-overview-stat relative rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-950/5 dark:bg-gray-900 dark:ring-white/10">
            <div class="flex items-center gap-x-4">
                <div class="flex-shrink-0 rounded-lg bg-primary-50 p-3 dark:bg-primary-400/10">
                    <svg class="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Dokumen</p>
                    <p class="text-2xl font-semibold text-gray-950 dark:text-white">{{ $stats['document_count'] ?? 0 }}</p>
                </div>
            </div>
        </div>
        
        <div class="fi-wi-stats-overview-stat relative rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-950/5 dark:bg-gray-900 dark:ring-white/10">
            <div class="flex items-center gap-x-4">
                <div class="flex-shrink-0 rounded-lg bg-success-50 p-3 dark:bg-success-400/10">
                    <svg class="h-6 w-6 text-success-600 dark:text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12l3 3 5-6"></path>
                    </svg>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Chunks</p>
                    <p class="text-2xl font-semibold text-gray-950 dark:text-white">{{ $stats['indexed_chunks'] ?? 0 }}</p>
                </div>
            </div>
        </div>
        
        <div class="fi-wi-stats-overview-stat relative rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-950/5 dark:bg-gray-900 dark:ring-white/10">
            <div class="flex items-center gap-x-4">
                <div class="flex-shrink-0 rounded-lg bg-warning-50 p-3 dark:bg-warning-400/10">
                    <svg class="h-6 w-6 text-warning-600 dark:text-warning-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Cache Hits</p>
                    <p class="text-2xl font-semibold text-gray-950 dark:text-white">{{ $stats['cache']['total_hits'] ?? 0 }}</p>
                </div>
            </div>
        </div>
        
        <div class="fi-wi-stats-overview-stat relative rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-950/5 dark:bg-gray-900 dark:ring-white/10">
            <div class="flex items-center gap-x-4">
                <div class="flex-shrink-0 rounded-lg bg-info-50 p-3 dark:bg-info-400/10">
                    <svg class="h-6 w-6 text-info-600 dark:text-info-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Sesi</p>
                    <p class="text-2xl font-semibold text-gray-950 dark:text-white">{{ $stats['total_sessions'] ?? 0 }}</p>
                </div>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {{-- Upload Section --}}
        <div class="lg:col-span-1">
            <x-filament::section>
                <x-slot name="heading">
                    <div class="flex items-center gap-2">
                        <svg class="h-5 w-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                        </svg>
                        <span>Upload Dokumen Baru</span>
                    </div>
                </x-slot>
                
                <div class="space-y-4">
                    {{ $this->form }}
                    
                    <div class="pt-2">
                        {{ $this->uploadAction }}
                    </div>
                </div>
                
                <div class="mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Format:</span> PDF, DOC, DOCX, MD, TXT
                    </p>
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Maks:</span> 10MB
                    </p>
                </div>
            </x-filament::section>
        </div>

        {{-- Documents List --}}
        <div class="lg:col-span-2">
            <x-filament::section>
                <x-slot name="heading">
                    <div class="flex items-center gap-2">
                        <svg class="h-5 w-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <span>Daftar Dokumen ({{ count($documents) }})</span>
                    </div>
                </x-slot>
                
                <x-slot name="headerEnd">
                    {{ $this->clearCacheAction }}
                </x-slot>

                @if(count($documents) > 0)
                    <div class="divide-y divide-gray-200 dark:divide-gray-700">
                        @foreach($documents as $doc)
                            @php
                                $filename = $doc['filename'] ?? '';
                                $originalName = $doc['original_name'] ?? '';
                                $displayName = pathinfo($filename, PATHINFO_FILENAME);
                                
                                // Check if original file is different and is a binary format
                                $hasBinaryOriginal = false;
                                $originalExt = '';
                                
                                if (!empty($originalName) && $originalName !== $filename) {
                                    $ext = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));
                                    if (in_array($ext, ['pdf', 'doc', 'docx'])) {
                                        $hasBinaryOriginal = true;
                                        $originalExt = strtoupper($ext);
                                    }
                                }
                            @endphp
                            <div wire:key="doc-{{ $loop->index }}" class="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                                <div class="flex items-center gap-4">
                                    <div class="flex-shrink-0 rounded-lg bg-primary-50 p-2.5 dark:bg-primary-400/10">
                                        <svg class="h-5 w-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
                                        </svg>
                                    </div>
                                    <div>
                                        <p class="font-medium text-gray-950 dark:text-white">{{ $displayName }}</p>
                                        <div class="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                                            <span class="inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700 dark:bg-primary-400/10 dark:text-primary-400">
                                                {{ $doc['category_name'] ?? 'Umum' }}
                                            </span>
                                            <span>{{ $doc['chunk_count'] ?? 0 }} chunks</span>
                                            <span>{{ number_format(($doc['file_size'] ?? 0) / 1024, 1) }} KB</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="flex items-center gap-2">
                                    {{-- View Dropdown --}}
                                    <x-filament::dropdown>
                                        <x-slot name="trigger">
                                            <x-filament::button color="gray" size="sm" icon="heroicon-o-eye" outlined>
                                                Lihat
                                            </x-filament::button>
                                        </x-slot>
                                        <x-filament::dropdown.list>
                                            <x-filament::dropdown.list.item 
                                                tag="a" 
                                                href="{{ $this->getPreviewUrl($filename) }}" 
                                                target="_blank"
                                                icon="heroicon-o-document-text"
                                            >
                                                File Markdown
                                            </x-filament::dropdown.list.item>
                                            @if($hasBinaryOriginal)
                                            <x-filament::dropdown.list.item 
                                                tag="a" 
                                                href="{{ $this->getPdfPreviewUrl($filename) }}" 
                                                target="_blank"
                                                icon="heroicon-o-document"
                                            >
                                                File Original ({{ $originalExt }})
                                            </x-filament::dropdown.list.item>
                                            @endif
                                        </x-filament::dropdown.list>
                                    </x-filament::dropdown>
                                    
                                    {{-- Download Dropdown --}}
                                    <x-filament::dropdown>
                                        <x-slot name="trigger">
                                            <x-filament::button color="warning" size="sm" icon="heroicon-o-arrow-down-tray" outlined>
                                                Download
                                            </x-filament::button>
                                        </x-slot>
                                        <x-filament::dropdown.list>
                                            <x-filament::dropdown.list.item 
                                                tag="a" 
                                                href="{{ $this->getPreviewUrl($filename) }}" 
                                                download="{{ $filename }}"
                                                icon="heroicon-o-document-text"
                                            >
                                                File Markdown
                                            </x-filament::dropdown.list.item>
                                            @if($hasBinaryOriginal)
                                            <x-filament::dropdown.list.item 
                                                tag="a" 
                                                href="{{ $this->getDocumentUrl($filename) }}" 
                                                download
                                                icon="heroicon-o-document"
                                            >
                                                File Original ({{ $originalExt }})
                                            </x-filament::dropdown.list.item>
                                            @endif
                                        </x-filament::dropdown.list>
                                    </x-filament::dropdown>
                                    
                                    {{-- Delete Button with Modal --}}
                                    <div x-data="{ open: false }">
                                        <x-filament::button
                                            color="danger"
                                            size="sm"
                                            icon="heroicon-o-trash"
                                            x-on:click="open = true"
                                            outlined
                                        >
                                            Hapus
                                        </x-filament::button>
                                        
                                        {{-- Modal Backdrop --}}
                                        <div 
                                            x-show="open" 
                                            x-cloak
                                            class="fixed inset-0 z-40 bg-black/50"
                                            x-on:click="open = false"
                                            x-transition:enter="ease-out duration-300"
                                            x-transition:enter-start="opacity-0"
                                            x-transition:enter-end="opacity-100"
                                            x-transition:leave="ease-in duration-200"
                                            x-transition:leave-start="opacity-100"
                                            x-transition:leave-end="opacity-0"
                                        ></div>
                                        
                                        {{-- Modal Content --}}
                                        <div 
                                            x-show="open" 
                                            x-cloak
                                            class="fixed inset-0 z-50 flex items-center justify-center p-4"
                                            x-transition:enter="ease-out duration-300"
                                            x-transition:enter-start="opacity-0 scale-95"
                                            x-transition:enter-end="opacity-100 scale-100"
                                            x-transition:leave="ease-in duration-200"
                                            x-transition:leave-start="opacity-100 scale-100"
                                            x-transition:leave-end="opacity-0 scale-95"
                                        >
                                            <div class="w-full max-w-md bg-white dark:bg-gray-900 rounded-xl shadow-xl" x-on:click.stop>
                                                {{-- Header --}}
                                                <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                                                    <div class="flex items-center gap-2 text-danger-600 dark:text-danger-400">
                                                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                                                        </svg>
                                                        <span class="text-lg font-semibold">Hapus Dokumen</span>
                                                    </div>
                                                </div>
                                                
                                                {{-- Body --}}
                                                <div class="p-4 space-y-3">
                                                    <p class="font-medium text-gray-900 dark:text-gray-100">{{ $displayName }}</p>
                                                    <div class="rounded-lg bg-danger-50 dark:bg-danger-900/20 p-3 text-sm text-danger-700 dark:text-danger-300">
                                                        <p class="font-medium mb-1">⚠️ Peringatan:</p>
                                                        <ul class="list-disc list-inside space-y-1">
                                                            <li>File markdown (.md) akan dihapus</li>
                                                            @if($hasBinaryOriginal)
                                                            <li>File original ({{ $originalExt }}) akan dihapus</li>
                                                            @endif
                                                            <li>Semua chunk di vector store akan dihapus</li>
                                                            <li>Data di database akan dihapus</li>
                                                        </ul>
                                                    </div>
                                                    <p class="text-sm text-gray-500 dark:text-gray-400">Tindakan ini tidak dapat dibatalkan.</p>
                                                </div>
                                                
                                                {{-- Footer --}}
                                                <div class="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
                                                    <x-filament::button color="gray" x-on:click="open = false">
                                                        Batal
                                                    </x-filament::button>
                                                    <x-filament::button 
                                                        color="danger" 
                                                        icon="heroicon-o-trash"
                                                        wire:click="deleteDocument('{{ $filename }}')"
                                                        x-on:click="open = false"
                                                        wire:loading.attr="disabled"
                                                    >
                                                        <span wire:loading.remove wire:target="deleteDocument('{{ $filename }}')">Ya, Hapus</span>
                                                        <span wire:loading wire:target="deleteDocument('{{ $filename }}')">Menghapus...</span>
                                                    </x-filament::button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        @endforeach
                    </div>
                @else
                    <div class="text-center py-12">
                        <div class="mx-auto h-16 w-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
                            <svg class="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                        </div>
                        <h3 class="text-sm font-medium text-gray-900 dark:text-white">Belum ada dokumen</h3>
                        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Upload dokumen pertama Anda untuk memulai!</p>
                    </div>
                @endif
            </x-filament::section>
        </div>
    </div>
</x-filament-panels::page>
