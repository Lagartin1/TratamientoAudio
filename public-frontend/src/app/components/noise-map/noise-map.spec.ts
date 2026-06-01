import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NoiseMap } from './noise-map';

describe('NoiseMap', () => {
  let component: NoiseMap;
  let fixture: ComponentFixture<NoiseMap>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NoiseMap],
    }).compileComponents();

    fixture = TestBed.createComponent(NoiseMap);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
