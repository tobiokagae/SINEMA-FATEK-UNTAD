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
                    <p class="text-2xl font-semibold text-gray-950 dark:text-white">{{ $stats['cache']['cache_hits'] ?? 0 }}</p>
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
                    <p class="text-2xl font-semibold text-gray-950 dark:text-white">{{ $stats['sessions']['total'] ?? 0 }}</p>
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
                
                <form wire:submit.prevent="upload" class="space-y-4">
                    {{ $this->form }}
                    
                    <x-filament::button type="submit" class="w-full" icon="heroicon-o-cloud-arrow-up">
                        Upload & Proses
                    </x-filament::button>
                </form>
                
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

                @if(count($documents) > 0)
                    <div class="divide-y divide-gray-200 dark:divide-gray-700">
                        @foreach($documents as $doc)
                            <div class="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                                <div class="flex items-center gap-4">
                                    <div class="flex-shrink-0 rounded-lg bg-primary-50 p-2.5 dark:bg-primary-400/10">
                                        @php
                                            $ext = pathinfo($doc['filename'] ?? '', PATHINFO_EXTENSION);
                                        @endphp
                                        @if($ext === 'pdf')
                                            <svg class="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                                                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
                                            </svg>
                                        @else
                                            <svg class="h-5 w-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                                                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
                                            </svg>
                                        @endif
                                    </div>
                                    <div>
                                        <p class="font-medium text-gray-950 dark:text-white">{{ $doc['filename'] ?? 'Unknown' }}</p>
                                        <div class="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                                            <span class="inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700 dark:bg-primary-400/10 dark:text-primary-400">
                                                {{ $doc['category_name'] ?? 'Umum' }}
                                            </span>
                                            <span>{{ $doc['chunk_count'] ?? 0 }} chunks</span>
                                            <span>{{ number_format(($doc['file_size'] ?? 0) / 1024, 1) }} KB</span>
                                        </div>
                                    </div>
                                </div>
                                <x-filament::button
                                    color="danger"
                                    size="sm"
                                    icon="heroicon-o-trash"
                                    wire:click="deleteDocument('{{ $doc['filename'] ?? '' }}')"
                                    wire:confirm="Yakin ingin menghapus dokumen ini?"
                                >
                                    Hapus
                                </x-filament::button>
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
