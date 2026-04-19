import { TestBed } from '@angular/core/testing';

import { Tecnico } from './tecnico';

describe('Tecnico', () => {
  let service: Tecnico;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Tecnico);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
